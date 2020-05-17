from typing import Optional, Any
from uuid import uuid4 as uuid
from dataclasses import dataclass, field
from structlog import get_logger
from jdb import (
    storage as db,
    membership as mbr,
    routing as rte,
    util,
    const as k,
)

_LOGGER = get_logger()


@dataclass
class Node:
    """represents the running node"""

    logger: Any = field(init=False)
    p2p_addr: str = ""
    client_addr: str = ""
    store: db.DB = field(init=False)
    name: Optional[str] = str(uuid())
    membership: mbr.Membership = field(init=False)
    router: "rte.Router" = field(init=False)

    def __iter__(self):
        """return meta"""

        for key in ["name", "p2p_addr", "client_addr"]:
            yield key, getattr(self, key)

        yield "membership", util.stringify_keys(dict(self.membership.cluster_state))

    def __post_init__(self):
        """override"""

        self.logger = _LOGGER.bind(name=self.name)
        self.store = db.DB()
        membership = mbr.Membership(node_name=self.name, node_addr=self.p2p_addr)
        self.membership = membership
        self.router = rte.Router(membership=membership, node=self)

    def coordinate(self, req: "rte.BatchRequest") -> db.Transaction:
        """handle a request i am responsible for"""

        self.logger.info(
            "node.coordinate.start", table=req.table, requests=req.requests
        )

        with self.store.transaction() as txn:
            for op in req.requests:
                if isinstance(op, rte.GetRequest):
                    txn.read(op.key)
                elif isinstance(op, rte.PutRequest):
                    txn.write(op.key, op.value)
                elif isinstance(op, rte.DeleteRequest):
                    txn.write(op.key, meta=k.BIT_TOMBSTONE)

        self.logger.info(
            "node.coordinate.done", table=req.table, returning=txn.returning
        )

        return txn

    def bootstrap(self, join: str):
        """contact peer, merge cluster states"""

        self.membership.bootstrap(join)
        self.logger.info("node.bootstrap", join=join)
