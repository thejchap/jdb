from __future__ import annotations
from collections import OrderedDict, MutableSet
from jdb import db as database, entry, util, types, errors


class Transaction:
    db: database.DB
    writes: OrderedDict[types.Key, entry.Entry]
    reads: MutableSet[types.Key]
    txnid: types.ID
    read_ts: types.Timestamp
    commit_ts: types.Timestamp

    def __init__(self, db: database.DB):
        self.db = db
        self.writes = OrderedDict()
        self.reads = set()
        self.txnid = util.gen_id()
        self.read_ts = db.oracle.read_ts()

    def read(self, key: types.Key) -> types.Value:
        if key in self.writes:
            return self.writes[key].value

        self.reads.add(key)

        seek = util.encode_key_with_ts(key, self.read_ts)
        version = self.db.read(seek)

        if not version or version.isdeleted:
            raise errors.NotFound()

        return version.value

    def write(self, key: types.Key, value: types.Value = bytes(), meta: int = 0):
        self.writes[key] = entry.Entry(key=key, value=value, meta=meta)

    def commit(self) -> Transaction:
        if not self.writes:
            return self

        commit_ts = self.db.oracle.commit_request(self)
        self.commit_ts = commit_ts
        writes = []

        for key, write in self.writes.items():
            key_with_ts = util.encode_key_with_ts(key=key, ts=commit_ts)
            new_entry = entry.Entry(key=key_with_ts, value=write.value, meta=write.meta)
            writes.append(new_entry)

        self.db.write(writes)

        return self
