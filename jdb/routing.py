from typing import Union, List
from dataclasses import dataclass, field
from structlog import get_logger

# pylint: disable=unused-import
from jdb import (
    membership as mbr,
    node as nde,
)
from jdb import errors as err, types as t, const as k, storage as db

LOGGER = get_logger()


@dataclass
class DeleteRequest:
    """request type"""

    key: t.Key


@dataclass
class PutRequest:
    """request type"""

    key: t.Key
    value: t.Value


@dataclass
class GetRequest:
    """request type"""

    key: t.Key


RequestUnion = Union[PutRequest, GetRequest, DeleteRequest]


@dataclass
class BatchResponse:
    """wrap response"""

    txn: db.TransactionMeta
    table: str


@dataclass
class BatchRequest:
    """represents a client request to get routed"""

    requests: List[RequestUnion] = field(default_factory=list)

    @property
    def table(self) -> str:
        """key that is used to route the request"""

        if not self.requests:
            raise err.InvalidRequest("no requests")

        match = k.REQ_KEY_REGEX.match(self.requests[0].key.decode())

        if not match:
            raise err.InvalidRequest("invalid key")

        table, _ = match.groups()
        return table


class Router:
    """handle request routing"""

    def __init__(self, membership: "mbr.Membership", node: "nde.Node"):
        self._membership = membership
        self._node = node

    def request(self, req: BatchRequest) -> BatchResponse:
        """send a request"""

        peer = self._membership.lookup_leaseholder(req.table)

        if not peer:
            LOGGER.info("routing.request.local", table=req.table)
            txn = self._node.coordinate(req)
            txnmeta = db.TransactionMeta(
                txnid=txn.txnid,
                read_ts=txn.read_ts,
                commit_ts=txn.commit_ts,
                returning=txn.returning,
                status=txn.status,
            )
            return BatchResponse(txn=txnmeta, table=req.table)

        LOGGER.info(
            "routing.request.remote",
            peer_name=peer.name,
            peer_addr=peer.addr,
            table=req.table,
        )

        return peer.coordinate(req)
