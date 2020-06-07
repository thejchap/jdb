from __future__ import annotations
from typing import Dict, Optional, Set, List
from contextlib import contextmanager
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from random import uniform, choice, sample
from time import sleep
from tenacity import retry, wait_fixed
from structlog import get_logger
import jdb.crdt as crdt
import jdb.util as util
import jdb.maglev as mag
import jdb.peer as pr

_LOGGER = get_logger()
_JITTER = 0.01
STARTUP_GRACE_PERIOD = 2
FD_INTERVAL = 0.5
FD_SUBGROUP_SIZE = 3
GOSSIP_SUBGROUP_SIZE = 5
GOSSIP_INTERVAL = 0.2


class Membership:
    """modified implementation of SWIM protocol"""

    def __init__(
        self,
        node_name: str,
        node_addr: str,
        failure_detection_interval: float = FD_INTERVAL,
        failure_detection_subgroup_size: int = FD_SUBGROUP_SIZE,
        gossip_subgroup_size: int = GOSSIP_SUBGROUP_SIZE,
        gossip_interval: float = GOSSIP_INTERVAL,
    ):
        self.failure_detection_subgroup_size = failure_detection_subgroup_size
        self.gossip_subgroup_size = gossip_subgroup_size
        self.failure_detection_interval = failure_detection_interval
        self.suspects: Set[str] = set()
        self._choices: Set[str] = set()
        self.suspect_queue: Queue = Queue()
        self.node_name = node_name
        self.node_addr = node_addr
        self.node_key = f"{node_name}={node_addr}"
        self.gossip_interval = gossip_interval
        self.cluster_state = crdt.LWWRegister(replica_id=node_name)
        self.cluster_state.add(self.node_key.encode())
        self.peers: Dict[str, pr.Peer] = {}
        self._build_route_table()
        self.logger = _LOGGER.bind(node=self.node_key)
        self.stopped = False
        self.lock = Lock()
        self.threads = [
            Thread(
                target=self._failure_detection_loop,
                daemon=True,
                name="MembershipFailureDetectionThread",
            ),
            Thread(
                target=self._gossip_loop, daemon=True, name="MembershipGossipThread"
            ),
            Thread(
                target=self._investigation_loop,
                daemon=True,
                name="MembershipInvestigationThread",
            ),
        ]

    @retry(wait=wait_fixed(1))
    def bootstrap(self, join: str):
        """initial state sync"""

        peer_name, addr = join.split("=")
        peer = self.add_peer(peer_name, addr)
        self._sync_with(peer)

    def _sync_with(self, peer: pr.Peer) -> crdt.LWWRegister:
        """some sugar"""

        merged = peer.membership_state_sync(
            self.cluster_state, from_addr=self.node_addr
        )

        return self.state_sync(merged, peer_addr=peer.addr)

    def add_peer(self, name: str, addr: str) -> pr.Peer:
        """add peer"""

        with self.lock:
            peer = pr.Peer(addr=addr, name=name, logger=self.logger)
            self.peers[name] = peer
            self.cluster_state.add(peer.node_key.encode())
            self._build_route_table()
            return peer

    def get_peer(self, name: str, addr: Optional[str]) -> pr.Peer:
        """get or add"""

        if name in self.peers:
            return self.peers[name]
        if addr:
            return self.add_peer(name, addr)

        raise Exception("unable to get or add peer")

    def remove_peer(self, peer: pr.Peer):
        """remove from map and cluster state"""

        with self.lock:
            self.cluster_state.remove(peer.node_key.encode())
            if peer.name in self.peers:
                del self.peers[peer.name]
            self._build_route_table()

    def _gossip_loop(self):
        """run forever"""

        while not self.stopped:
            self._gossip()

            sleep(
                uniform(self.gossip_interval - _JITTER, self.gossip_interval + _JITTER)
            )

    def _probe_random_peer(self):
        """pick a rando from the group and probe it"""

        target = self._random_peer()

        if not target:
            return

        self.logger.info("membership.probe", peer=target.node_key)

        with self._failure_detection(target):
            target.membership_ping()

    def _gossip(self):
        """pick k randos from the group and sync with them"""

        keys = self._gossip_subgroup()

        if not keys:
            return

        peers: List[pr.Peer] = []

        for key in keys:
            peer_name, addr = key.split("=")
            peer = self.get_peer(peer_name, addr=addr)
            peers.append(peer)

        self.logger.info("membership.gossip", peers=[p.node_key for p in peers])

        with ThreadPoolExecutor(max_workers=5) as e:
            for peer in peers:
                task = e.submit(self._sync_with, peer)

                with self._failure_detection(peer):
                    task.result()

    def _failure_detection_loop(self):
        """SWIM fd sort of"""

        while not self.stopped:
            self._probe_random_peer()

            sleep(
                uniform(
                    self.failure_detection_interval - _JITTER,
                    self.failure_detection_interval + _JITTER,
                )
            )

    def _investigation_loop(self):
        """process suspects off suspect queue"""

        while not self.stopped:
            suspect = self.suspect_queue.get()

            if suspect is None:
                break

            self._investigate(suspect)
            self.suspect_queue.task_done()

    def _investigate(self, suspect: pr.Peer):
        """indirectly probe suspect. todo: make async"""

        keys = self._failure_detection_subgroup()
        investigators: List[pr.Peer] = []

        for key in keys:
            name, addr = key.split("=")
            peer = self.get_peer(name, addr=addr)
            investigators.append(peer)

        self.logger.info(
            "membership.investigating",
            peer=suspect.node_key,
            investigators=[i.node_key for i in investigators],
        )

        results = {}

        with ThreadPoolExecutor(max_workers=5) as e:
            for peer in investigators:
                task = e.submit(peer.membership_ping_req, suspect)
                results[peer] = task.result()

        for peer, ack in results.items():
            if not ack:
                continue
            self._failure_vetoed(suspect, by_peer=peer)
            return

        self._failure_confirmed(suspect, by_peers=investigators)

    def _failure_vetoed(self, suspect: pr.Peer, by_peer: pr.Peer):
        """another node was able to contact the suspect"""

        self.logger.info(
            "membership.failure_vetoed", peer=suspect.node_key, by=by_peer.node_key
        )

        if suspect.node_key in self.suspects:
            self.suspects.remove(suspect.node_key)

    def _failure_confirmed(self, suspect: pr.Peer, by_peers: List[pr.Peer]):
        """its actually faulty, update and disseminate"""

        self.logger.info(
            "membership.failure_confirmed",
            peer=suspect.node_key,
            by=list(map(lambda p: p.node_key, by_peers)),
        )

        self.remove_peer(suspect)

        if suspect.node_key in self.suspects:
            self.suspects.remove(suspect.node_key)

        self._gossip()

    def _gossip_subgroup(self) -> List[str]:
        """grab k non-faulty peers for gossip"""

        peers = self._eligible_peers()
        k = min(self.gossip_subgroup_size, len(peers))
        return sample(self._eligible_peers(), k=k,)

    def _failure_detection_subgroup(self) -> List[str]:
        """grab k non-faulty peers for failure verification"""

        peers = self._eligible_peers()
        k = min(self.failure_detection_subgroup_size, len(peers))
        return sample(self._eligible_peers(), k=k)

    @contextmanager
    def _failure_detection(self, peer: pr.Peer):
        """meant to wrap a rpc call, if it fails, investigate peer"""

        try:
            yield
        except Exception:  # pylint: disable=broad-except
            self._add_suspect(peer)

    def _add_suspect(self, peer: pr.Peer):
        """mark as suspect, publish to queue"""

        self.suspects.add(peer.node_key)
        self.suspect_queue.put(peer)
        self.logger.info("membership.add_suspect", peer=peer.node_key)

    def _random_peer(self) -> Optional[pr.Peer]:
        """pick a random peer from cluster state"""

        peers = self._eligible_peers()

        if len(self._choices) >= len(peers):
            self._choices = set()

        filtered = [i for i in peers if i not in self._choices]

        if not filtered:
            return None

        key = choice(filtered)
        self._choices.add(key)
        name, addr = key.split("=")
        return self.get_peer(name=name, addr=addr)

    def _eligible_peers(self) -> List[str]:
        """
        list of peers eligible for comms, filtering out this node and ones
        that we are still giving some time to start up
        """

        all_peers = dict(self.cluster_state).items()
        my_key = self.node_key.encode()
        counter_pad = 100
        now = util.now_ms() * counter_pad
        i = STARTUP_GRACE_PERIOD * 1000 * counter_pad

        return [
            k.decode()
            for k, v in all_peers
            if k != my_key and (v + i) < now and k.decode() not in self.suspects
        ]

    def ping(self, peer_name: str, peer_addr: str) -> bool:
        """ping a given peer"""

        peer = self.get_peer(peer_name, addr=peer_addr)
        return peer.membership_ping()

    def ping_req(self, peer_name: str, peer_addr: str) -> bool:
        """handle a ping request from a peer"""

        peer = self.get_peer(peer_name, addr=peer_addr)

        with self._failure_detection(peer):
            return peer.membership_ping()

    def state_sync(
        self, incoming: crdt.LWWRegister, peer_addr: str
    ) -> crdt.LWWRegister:
        """take another nodes cluster state and merge with our own"""

        self.get_peer(incoming.replica_id, addr=peer_addr)

        with self.lock:
            res = self.cluster_state.merge(incoming)
            self._build_route_table()

        return res

    def _build_route_table(self):
        """rebuild rt"""

        nodekeys = map(lambda k: k[0].decode().split("=")[0], self.cluster_state)
        self.maglev = mag.Maglev(nodes=set(nodekeys))

    def lookup_leaseholder(self, key: str) -> Optional[pr.Peer]:
        """find whos responsible for a key. if self, return None"""

        name = self.maglev.lookup(key)
        return self.peers.get(name)

    def stop(self):
        """shut down"""

        self.suspect_queue.put(None)
        self.stopped = True
        for thread in self.threads:
            thread.join()
        self.logger.info("membership.stop")

    def start(self):
        """fire up all components"""

        for thread in self.threads:
            thread.start()

        self.logger.info("membership.start")

        for thread in self.threads:
            thread.join()
