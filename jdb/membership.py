from __future__ import annotations
from typing import Any, Dict, Optional, Set, List
from contextlib import contextmanager
from threading import Thread
from queue import Queue
from random import uniform, choice, choices
from time import sleep
import grpc
from tenacity import retry, wait_fixed
from structlog import get_logger
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb
from jdb import crdt, types, util

_LOGGER = get_logger()
_JITTER = 0.05
_STARTUP_GRACE_PERIOD = 2


class Peer:
    """represents remote peer"""

    def __init__(self, addr: str, node_id: types.ID, logger: Any):
        self.addr = addr
        self.node_id = node_id
        self.logger = logger.bind(peer_id=util.id_to_str(node_id), peer_addr=addr)
        self.channel = grpc.insecure_channel(self.addr)
        self.transport = pgrpc.PeerServerStub(self.channel)

    @property
    def node_key(self) -> str:
        """concatenation, pretty much all the data we need for a peer"""

        return f"{self.node_id}={self.addr}"

    def membership_ping(self) -> bool:
        """ping"""

        msg = pb.Empty()
        self.transport.MembershipPing(msg)
        return True

    def membership_ping_req(self, _other: Peer) -> bool:
        """ping"""

        msg = pb.Empty()

        try:
            self.transport.MembershipPingReq(msg)
        except Exception:
            return False

        return True

    def membership_state_sync(
        self, state: crdt.LWWRegister, from_addr: str
    ) -> crdt.LWWRegister:
        """rpc call wrapper"""

        req = pb.MembershipState(
            add_set=state.add_set,
            remove_set=state.remove_set,
            replica_id=state.replica_id,
            peer_addr=from_addr,
        )

        res = self.transport.MembershipStateSync(req)
        merged = crdt.LWWRegister(replica_id=res.replica_id)
        merged.add_set = util.byteify_keys(res.add_set)
        merged.remove_set = util.byteify_keys(res.remove_set)
        return merged


class Membership:
    """modified implementation of SWIM protocol"""

    def __init__(
        self,
        node_id: types.ID,
        node_addr: str,
        failure_detection_interval: float = 1,
        failure_detection_subgroup_size: int = 3,
        gossip_interval: float = 0.2,
        sync_interval: float = 2,
    ):
        self.failure_detection_subgroup_size = failure_detection_subgroup_size
        self.failure_detection_interval = failure_detection_interval
        self.gossip_interval = gossip_interval
        self.suspects: Set[str] = set()
        self.suspect_queue: Queue = Queue()
        self.node_id = node_id
        self.node_addr = node_addr
        self.node_key = f"{node_id}={node_addr}"
        self.sync_interval = sync_interval
        self.cluster_state = crdt.LWWRegister(replica_id=node_id)
        self.cluster_state.add(self.node_key.encode())
        self.peers: Dict[types.ID, Peer] = {}
        self.logger = _LOGGER

    @retry(wait=wait_fixed(1))
    def bootstrap(self, join: str):
        """initial state sync"""

        peer_id_str, addr = join.split("=")
        peer_id = util.id_from_str(peer_id_str)
        peer = self._get_peer(peer_id, addr)
        self._sync_with(peer)

    def _sync_with(self, peer: Peer) -> crdt.LWWRegister:
        """some sugar"""

        merged = peer.membership_state_sync(
            self.cluster_state, from_addr=self.node_addr
        )
        return self.state_sync(merged, peer_addr=peer.addr)

    def _get_peer(self, peer_id: types.ID, addr: str) -> Peer:
        """not sure about this yet"""

        if peer_id in self.peers:
            return self.peers[peer_id]

        peer = Peer(addr=addr, node_id=peer_id, logger=self.logger)
        self.peers[peer_id] = peer
        self.cluster_state.add(peer.node_key.encode())
        self.logger.info("membership.peer_added", peer=peer.node_key)

        return peer

    def _remove_peer(self, peer: Peer):
        """remove from map and cluster state"""

        self.cluster_state.remove(peer.node_key.encode())
        del self.peers[peer.node_id]
        self.logger.info("membership.peer_removed", peer=peer.node_key)

    def _sync_loop(self):
        """run forever"""

        while True:
            self._sync_with_random_peer()
            sleep(uniform(self.sync_interval - _JITTER, self.sync_interval + _JITTER))

    def _sync_with_random_peer(self):
        """pick a rando from the group and sync with it"""

        target = self._random_peer()

        if not target:
            return

        with self._failure_detection(target):
            self._sync_with(target)

        self.logger.info("membership.sync", peer=target.node_key)

    def _investigation_loop(self):
        """process suspects off suspect queue"""

        while True:
            suspect = self.suspect_queue.get()

            if suspect is None:
                break

            self._investigate(suspect)
            self.suspect_queue.task_done()

    def _investigate(self, suspect: Peer):
        """indirectly probe suspect"""

        self.logger.info("membership.investigating", peer=suspect.node_key)

        keys = self._failure_detection_subgroup()
        investigators: List[Peer] = []

        for key in keys:
            peer_id, addr = key.split("=")
            peer = self._get_peer(util.id_from_str(peer_id), addr=addr)
            investigators.append(peer)

        for peer in investigators:
            ack = peer.membership_ping_req(suspect)

            if ack:
                self._failure_vetoed(suspect, by=peer)
                return

        self._failure_confirmed(suspect, by=investigators)

    def _failure_vetoed(self, suspect: Peer, by: Peer):
        """another node was able to contact the suspect"""

        self.logger.info(
            "membership.failure_vetoed", peer=suspect.node_key, by=by.node_key
        )
        self.suspects.remove(suspect.node_key)

    def _failure_confirmed(self, suspect: Peer, by: List[Peer]):
        """its actually faulty, update and disseminate"""

        self.logger.info(
            "membership.failure_confirmed",
            peer=suspect.node_key,
            by=list(map(lambda p: p.node_key, by)),
        )

        self._remove_peer(suspect)
        self.suspects.remove(suspect.node_key)

    def _failure_detection_subgroup(self) -> List[str]:
        """grab k non-faulty peers"""

        peers = self._eligible_peers()

        return choices(
            self._eligible_peers(),
            k=min(self.failure_detection_subgroup_size, len(peers)),
        )

    @contextmanager
    def _failure_detection(self, peer: Peer):
        """meant to wrap a rpc call, if it fails, investigate peer"""

        try:
            yield
        except Exception:  # pylint: disable=broad-except
            self._add_suspect(peer)

    def _add_suspect(self, peer: Peer):
        """mark as suspect, publish to queue"""

        self.suspects.add(peer.node_key)
        self.suspect_queue.put(peer)
        self.logger.info("membership.add_suspect", peer=peer.node_key)

    def _random_peer(self) -> Optional[Peer]:
        """pick a random peer from cluster state"""

        filtered = self._eligible_peers()

        if not filtered:
            return None

        key = choice(filtered)
        peer_id, addr = key.split("=")
        return self._get_peer(peer_id=util.id_from_str(peer_id), addr=addr)

    def _eligible_peers(self) -> List[str]:
        """
        list of peers eligible for comms, filtering out this node and ones
        that we are still giving some time to start up
        """

        all_peers = dict(self.cluster_state).items()
        my_key = self.node_key.encode()
        now = util.now_ms() * 100  # factor in counter
        i = _STARTUP_GRACE_PERIOD * 1000 * 100  # factor in counter

        return [
            k.decode()
            for k, v in all_peers
            if k != my_key and (v + i) < now and k.decode() not in self.suspects
        ]

    def state_sync(
        self, incoming: crdt.LWWRegister, peer_addr: str
    ) -> crdt.LWWRegister:
        """take another nodes cluster state and merge with our own"""

        self._get_peer(incoming.replica_id, addr=peer_addr)
        return self.cluster_state.merge(incoming)

    def start(self):
        """fire up all components"""

        threads = [
            Thread(target=self._sync_loop, daemon=True, name="MembershipSyncThread"),
            Thread(
                target=self._investigation_loop,
                daemon=True,
                name="MembershipInvestigationThread",
            ),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
