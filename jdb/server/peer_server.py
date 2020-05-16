from typing import Tuple
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from structlog import get_logger
import grpc
from jdb import node as nde, crdt, util, routing as rte, errors as err
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb

_LOGGER = get_logger()


class PeerServer(pgrpc.PeerServerServicer):
    """server for p2p communication"""

    def Coordinate(self, request, context):
        req = rte.BatchRequest()

        for re in request.requests:
            which = re.WhichOneof("value")

            if which == "put":
                req.requests.append(rte.PutRequest(re.put.key, re.put.value))
            elif which == "get":
                req.requests.append(rte.GetRequest(re.get.key))
            elif which == "delete":
                req.requests.append(rte.DeleteRequest(re.delete.key))

        try:
            returning = self.node.coordinate(req)
        except err.NotFound:
            returning = {}

        return pb.BatchResponse(key=request.key, returning=returning)

    def MembershipPing(self, request, context):
        return pb.Ack(ack=True)

    def MembershipPingReq(self, request, context):
        try:
            self.node.membership.ping(request.peer_name, request.peer_addr)
        except Exception:  # pylint: disable=broad-except
            return pb.Ack(ack=False)

        return pb.Ack(ack=True)

    def MembershipStateSync(self, request, context):
        incoming = crdt.LWWRegister(replica_id=request.replica_id)
        incoming.add_set = util.byteify_keys(request.add_set)
        incoming.remove_set = util.byteify_keys(request.remove_set)
        state = self.node.membership.state_sync(incoming, peer_addr=request.peer_addr)

        return pb.MembershipState(
            replica_id=self.node.name,
            peer_addr=self.node.p2p_addr,
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
