from dataclasses import dataclass, field
from jdb import db, types, util, crdt


@dataclass
class Node:
    database: db.DB = db.DB()
    node_id: types.ID = util.gen_id()
    peers: crdt.LWWRegister = field(init=False)

    def __post_init__(self):
        self.peers = crdt.LWWRegister(replica_id=self.node_id)
