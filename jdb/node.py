from typing import Optional
from jdb import db, util, crdt, types


class Node:
    def __init__(self, node_id: Optional[types.ID] = None):
        self.database = db.DB()
        self.node_id = node_id or util.gen_id()
        self.peers = crdt.LWWRegister(replica_id=self.node_id)
