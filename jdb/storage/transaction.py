from __future__ import annotations
from collections import OrderedDict
from typing import MutableSet, Dict
from jdb.storage import db as database, entry as ent
from jdb import util, types, errors


class Transaction:
    """represents a db transaction"""

    db: database.DB
    writes: OrderedDict
    reads: MutableSet[types.Key]
    txnid: types.ID
    read_ts: types.Timestamp
    commit_ts: types.Timestamp

    def __init__(self, db: database.DB):
        self.db = db
        self.writes = OrderedDict()
        self.reads = set()
        self.returning: Dict[types.Key, types.Value] = {}
        self.txnid = util.gen_id()
        self.read_ts = db.oracle.read_ts()

    def read(self, key: types.Key) -> types.Value:
        """
        if this transaction has any writes for this key, fulfill from there.
        else, load latest version from its snapshot of the db and track the
        read key
        """

        if key in self.writes:
            return self.writes[key].value

        self.reads.add(key)

        seek = util.encode_key_with_ts(key, self.read_ts)
        version = self.db.read(seek)

        if not version or version.isdeleted:
            raise errors.NotFound()

        self.returning[key] = version.value
        return version.value

    def write(self, key: types.Key, value: types.Value = bytes(), meta: int = 0):
        """add a pending write"""

        self.writes[key] = ent.Entry(key=key, value=value, meta=meta)

    def commit(self) -> Transaction:
        """
        dont incur any overhead with oracle if no writes to process.
        else, get a commit ts from oracle and apply to all writes then ship
        over to db to persist
        """

        if not self.writes:
            return self

        with self.db.oracle.write_lock:
            return self._commit()

    def _commit(self) -> Transaction:
        """we have writes, commit transaction"""

        commit_ts = self.db.oracle.commit_request(self)
        self.commit_ts = commit_ts
        writes = []

        for key, write in self.writes.items():
            key_with_ts = util.encode_key_with_ts(key=key, ts=commit_ts)
            new_entry = ent.Entry(key=key_with_ts, value=write.value, meta=write.meta)
            writes.append(new_entry)

        self.db.write(writes)

        return self
