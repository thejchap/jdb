from typing import Optional, Any
from dataclasses import dataclass, field
from structlog import get_logger
from jdb import db, util, types, membership as mbr

_LOGGER = get_logger()


@dataclass
class Node:
    """represents the running node"""

    logger: Any = field(init=False)
    p2p_addr: str = ""
    client_addr: str = ""
    store: db.DB = field(init=False)
    node_id: Optional[types.ID] = None
    membership: mbr.Membership = field(init=False)

    def __iter__(self):
        """return meta"""

        yield "node_id", util.id_to_str(self.node_id)

        for key in ["p2p_addr", "client_addr"]:
            yield key, getattr(self, key)

        yield "membership", util.stringify_keys(dict(self.membership.cluster_state))

    def __post_init__(self):
        """override"""

        if not self.node_id:
            self.node_id = util.gen_id()

        self.logger = _LOGGER.bind(node_id=util.id_to_str(self.node_id))
        self.store = db.DB()
        self.membership = mbr.Membership(node_id=self.node_id, node_addr=self.p2p_addr)
        self.logger.info("node.initialized")

    def bootstrap(self, join: str):
        """contact peer, merge cluster states"""
        self.membership.bootstrap(join)
        self.logger.info("node.bootstrap", join=join)
