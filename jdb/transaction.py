from typing import List, Set
from .entry import Entry
from .db import DB
from .id import gen_id, ID


class Read:
    def __init__(self, key: bytes):
        self.key = key


class Transaction:
    db: DB
    writes: List[Entry]
    reads: List[Read]
    txnid: ID
    read_ts: int
    commit_ts: int

    def __init__(self, db: DB):
        self.db = db
        self.writes = []
        self.reads = []
        self.txnid = gen_id()
        self.read_ts = db.oracle.read_ts()

    @property
    def write_set(self) -> Set:
        return set([w.key for w in self.writes])

    @property
    def read_set(self) -> Set:
        return set([w.key for w in self.reads])

    def commit(self):
        commit_ts = self.db.oracle.commit_request(self)
        self.commit_ts = commit_ts

        for entry in self.writes:
            self.db.append(entry)

        return self
