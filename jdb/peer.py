from __future__ import annotations
from typing import Any, Dict
import grpc
from jdb.pb import peer_server_pb2_grpc as pgrpc, peer_server_pb2 as pb
from jdb import crdt, util, routing as rte, types


class Peer:
    """represents remote peer"""

    def __init__(self, addr: str, name: str, logger: Any):
        self.addr = addr
        self.name = name
        self.logger = logger.bind(name=name, addr=addr)
        self.channel = grpc.insecure_channel(self.addr)
        self.transport = pgrpc.PeerServerStub(self.channel)

    @property
    def node_key(self) -> str:
        """concatenation, pretty much all the data we need for a peer"""

        return f"{self.name}={self.addr}"

    def coordinate(self, req: rte.BatchRequest) -> Dict[types.Key, types.Value]:
        """coordinate"""

        requests = []

        for re in req.requests:
            if isinstance(re, rte.PutRequest):
                val = pb.PutRequest(key=re.key, value=re.value)
                requests.append(pb.RequestUnion(put=val))
            elif isinstance(re, rte.GetRequest):
                val = pb.GetRequest(key=re.key)
                requests.append(pb.RequestUnion(get=val))
            elif isinstance(re, rte.DeleteRequest):
                val = pb.DeleteRequest(key=re.key)
                requests.append(pb.RequestUnion(delete=val))

        msg = pb.BatchRequest(key=req.key, requests=requests)
        res = self.transport.Coordinate(msg)
        return {k.encode(): v.encode() for k, v in res.returning.items()}

    def membership_ping(self) -> bool:
        """ping"""

        msg = pb.Empty()

        try:
            ack = self.transport.MembershipPing(msg)
            return ack.ack
        except Exception:  # pylint: disable=broad-except
            return False

    def membership_ping_req(self, other: Peer) -> bool:
        """ping"""

        msg = pb.MembershipPingRequest(peer_name=other.name, peer_addr=other.addr)

        try:
            res = self.transport.MembershipPingReq(msg)
            return res.ack
        except Exception:  # pylint: disable=broad-except
            return False

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
