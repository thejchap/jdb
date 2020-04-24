from typing import Tuple
from time import sleep
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from structlog import get_logger
import grpc
from jdb import node as nde, crdt
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb

_LOGGER = get_logger()


class PeerServer(pgrpc.PeerServerServicer):
    """server for p2p communication"""

    def MembershipPing(self, request, context):
        return pb.Empty()

    def MembershipStateSync(self, request, context):
        incoming = crdt.LWWRegister(replica_id=request.replica_id)
        incoming.add_set = OrderedDict({k: int(v) for k, v in request.add_set.items()})
        incoming.remove_set = OrderedDict(
            {k: int(v) for k, v in request.remove_set.items()}
        )

        merged = self.node.membership_state_sync(incoming)

        return pb.MembershipState(
            add_set=merged.add_set,
            remove_set=merged.remove_set,
            replica_id=self.node.node_id,
        )

    def __init__(self, addr: Tuple[str, int], node: nde.Node):
        super().__init__()

        addr_str = ":".join(map(str, addr))
        self.node = node
        self.logger = _LOGGER.bind(addr=addr_str)
        self.addr = addr

        server = grpc.server(ThreadPoolExecutor(10))
        pgrpc.add_PeerServerServicer_to_server(self, server)
        server.add_insecure_port(addr_str)

        self.server = server

    def serve_forever(self):
        """start it up"""

        self.server.start()
        self.logger.msg("peer_server.listening")

        while True:
            sleep(1)

    def shutdown(self):
        """shut it down"""

        self.logger.msg("peer_server.shutdown")
        self.server.stop(1)
