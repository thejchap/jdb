from typing import Any, Dict
from threading import Thread
from random import uniform
from time import sleep
import grpc
from tenacity import retry, wait_fixed
from structlog import get_logger
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb
from jdb import crdt, types, util

_LOGGER = get_logger()
_JITTER = 0.05


class Peer:
    """represents remote peer"""

    def __init__(self, addr: str, node_id: types.ID, logger: Any):
        self.addr = addr
        self.node_id = node_id
        self.logger = logger.bind(peer_id=util.id_to_str(node_id), peer_addr=addr)
        self.channel = grpc.insecure_channel(self.addr)
        self.transport = pgrpc.PeerServerStub(self.channel)

    def membership_ping(self) -> bool:
        """ping"""

        msg = pb.Empty()
        self.transport.MembershipPing(msg)
        return True

    def membership_state_sync(self, state: crdt.LWWRegister) -> crdt.LWWRegister:
        """rpc call wrapper"""

        req = pb.MembershipState(
            add_set=state.add_set,
            remove_set=state.remove_set,
            replica_id=state.replica_id,
        )

        res = self.transport.MembershipStateSync(req)
        merged = crdt.LWWRegister(replica_id=res.replica_id)
        merged.add_set = util.byteify_keys(res.add_set)
        merged.remove_set = util.byteify_keys(res.remove_set)
        return merged


class FailureDetector:
    """
    detect failures.
    1. pick a peer at random every interval
    2. probe it
    3. if ack, continue
    4. if error, ask nodes in subgroup to probe it
    5. if any of them can contact it, continue
    6. if all fail, add to failed
    """

    def __init__(self, interval: float, subgroup_size: int, logger: Any):
        self.interval = interval
        self.subgroup_size = subgroup_size
        self.logger = logger

    def loop(self):
        """main loop"""

        while True:
            sleep(uniform(self.interval - _JITTER, self.interval + _JITTER))


class Dissemination:
    """gossip with other nodes"""

    def __init__(self, interval: float, logger: Any):
        self.interval = interval
        self.logger = logger

    def loop(self):
        """main loop"""

        while True:
            sleep(uniform(self.interval - _JITTER, self.interval + _JITTER))


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
        self.sync_interval = sync_interval
        self.cluster_state = crdt.LWWRegister(replica_id=node_id)
        self.cluster_state.add(f"{node_id}={node_addr}".encode())
        self.peers: Dict[types.ID, Peer] = {}
        self.logger = _LOGGER.bind(node_id=node_id)
        self._dissemination = Dissemination(
            interval=gossip_interval, logger=self.logger
        )
        self._failure_detector = FailureDetector(
            interval=failure_detection_interval,
            subgroup_size=failure_detection_subgroup_size,
            logger=self.logger,
        )

    @retry(wait=wait_fixed(1))
    def bootstrap(self, join: str):
        """initial state sync"""

        peer_id_str, addr = join.split("=")
        peer_id = util.id_from_str(peer_id_str)
        peer = self._add_peer(peer_id, addr)
        merged = peer.membership_state_sync(self.cluster_state)
        self.state_sync(merged)

    def _add_peer(self, peer_id: types.ID, addr: str) -> Peer:
        """not sure about this yet"""

        if peer_id in self.peers:
            return self.peers[peer_id]

        peer = Peer(addr=addr, node_id=peer_id, logger=self.logger)
        self.peers[peer_id] = peer
        return peer

    def _sync_loop(self):
        while True:
            self._sync_with_random_peer()
            sleep(uniform(self.sync_interval - _JITTER, self.sync_interval + _JITTER))

    def _sync_with_random_peer(self):
        self.logger.info("membership.sync")

    def state_sync(self, incoming: crdt.LWWRegister) -> crdt.LWWRegister:
        """take another nodes cluster state and merge with our own"""

        return self.cluster_state.merge(incoming)

    def start(self):
        """fire up both components"""

        threads = [
            Thread(
                target=self._failure_detector.loop,
                daemon=True,
                name="MembershipFailureDetectorThread",
            ),
            Thread(
                target=self._dissemination.loop,
                daemon=True,
                name="MembershipDisseminationThread",
            ),
            Thread(target=self._sync_loop, daemon=True, name="MembershipSyncThread",),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
