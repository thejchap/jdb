from typing import List
from jdb.entry import Entry
from jdb.db import DB
from jdb.id import gen_id, ID


class Read:
    def __init__(self, key: bytes):
        self.key = key


class Transaction:
    db: DB
    entries: List[Entry]
    reads: List[Read]
    txnid: ID

    def __init__(self, db: DB):
        self.db = db
        self.entries = []
        self.reads = []
        self.txnid = gen_id()

    def commit(self):
        for entry in self.entries:
            self.db.append(entry)

        return self
