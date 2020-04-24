from typing import Optional, Any
from dataclasses import dataclass, field
from collections import OrderedDict
from structlog import get_logger
import grpc
from tenacity import retry, wait_fixed
from jdb import db, util, crdt, types
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb

_LOGGER = get_logger()


class Peer:
    """represents remote peer"""

    def __init__(self, addr: str, node_id: types.ID, logger: Any):
        self.channel = grpc.insecure_channel(addr)
        self.addr = addr
        self.node_id = node_id
        self.logger = logger.bind(peer_id=util.id_to_str(node_id), peer_addr=addr)
        self._transport = pgrpc.PeerServerStub(self.channel)

    def membership_state_sync(
        self, cluster_state: crdt.LWWRegister
    ) -> crdt.LWWRegister:
        """wrapper around rpc call"""

        self.logger.info("node.membership_state_sync.start")

        msg = pb.MembershipState(
            add_set=cluster_state.add_set, remove_set=cluster_state.remove_set
        )

        res = self._transport.MembershipStateSync(msg)
        merged = crdt.LWWRegister(replica_id=self.node_id)
        merged.add_set = OrderedDict({k: int(v) for k, v in res.add_set.items()})
        merged.remove_set = OrderedDict({k: int(v) for k, v in res.remove_set.items()})

        self.logger.info("node.membership_state_sync.done")

        return merged


@dataclass
class Node:
    """represents the running node"""

    logger: Any = field(init=False)
    p2p_addr: str
    client_addr: str
    store: db.DB = field(init=False)
    node_id: Optional[types.ID] = None
    cluster_state: crdt.LWWRegister = field(init=False)

    def __iter__(self):
        """return meta"""

        for key in ["p2p_addr", "client_addr", "node_id"]:
            yield key, getattr(self, key)

        yield "cluster_state", dict(self.cluster_state)

    def __post_init__(self):
        """override"""

        if not self.node_id:
            self.node_id = util.gen_id()

        self.logger = _LOGGER.bind(node_id=util.id_to_str(self.node_id))
        self.store = db.DB()
        self.cluster_state = crdt.LWWRegister(replica_id=self.node_id)
        self.cluster_state.add(f"{util.id_to_str(self.node_id)}={self.p2p_addr}")
        self.logger.info("node.initialized")

    @retry(wait=wait_fixed(1))
    def bootstrap(self, join: str):
        """contact peer, merge cluster states"""

        node_id, addr = join.split("=")
        self.logger.info("node.bootstrap.start")
        peer = Peer(addr=addr, node_id=util.id_from_str(node_id), logger=self.logger)
        merged = peer.membership_state_sync(self.cluster_state)
        self.cluster_state = merged
        self.logger.info("node.bootstrap.done")
