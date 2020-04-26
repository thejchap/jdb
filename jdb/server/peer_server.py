from typing import Tuple
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from structlog import get_logger
import grpc
from jdb import node as nde, crdt, util
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb

_LOGGER = get_logger()


class PeerServer(pgrpc.PeerServerServicer):
    """server for p2p communication"""

    def MembershipPing(self, request, context):
        return pb.Empty()

    def MembershipStateSync(self, request, context):
        incoming = crdt.LWWRegister(replica_id=request.replica_id)
        incoming.add_set = util.byteify_keys(request.add_set)
        incoming.remove_set = util.byteify_keys(request.remove_set)
        state = self.node.membership.state_sync(incoming)
        print(dict(self.node.membership.cluster_state))

        return pb.MembershipState(
            replica_id=state.replica_id,
            remove_set=state.remove_set,
            add_set=state.add_set,
        )

    def __init__(self, addr: Tuple[str, int], node: nde.Node):
        super().__init__()

        addr_str = ":".join(map(str, addr))
        self.node = node
        self.logger = _LOGGER.bind(addr=addr_str)
        self.addr = addr

        server = grpc.server(
            ThreadPoolExecutor(10, thread_name_prefix="PeerServerThreadPool")
        )

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
