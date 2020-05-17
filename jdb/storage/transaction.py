from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, MutableSet, Dict
from uuid import uuid4 as uuid
from enum import Enum
from collections import OrderedDict
from jdb import util, types as t, storage, errors as err


class TransactionStatus(Enum):
    """"what state txn is in"""

    PENDING = 0
    COMMITTED = 1
    ABORTED = 2
    NOOP = 3


@dataclass
class TransactionMeta:
    """data only. TODO refactor"""

    txnid: str
    read_ts: t.Timestamp
    commit_ts: Optional[t.Timestamp]
    status: TransactionStatus
    returning: t.Returning

    @property
    def ispending(self) -> bool:
        """helper"""

        return self.status == TransactionStatus.PENDING

    @property
    def isaborted(self) -> bool:
        """helper"""

        return self.status == TransactionStatus.ABORTED

    @property
    def iscommitted(self) -> bool:
        """helper"""

        return self.status == TransactionStatus.COMMITTED


class Transaction:
    """represents a db transaction"""

    db: storage.DB
    writes: OrderedDict
    reads: MutableSet[t.Key]
    txnid: str
    read_ts: t.Timestamp
    commit_ts: Optional[t.Timestamp]
    status: TransactionStatus

    def __init__(self, db: storage.DB):
        self.db = db
        self.writes = OrderedDict()
        self.reads = set()
        self.returning: Dict[t.Key, Optional[t.Value]] = {}
        self.txnid = str(uuid())
        self.read_ts = db.oracle.read_ts()
        self.commit_ts = None
        self.status = TransactionStatus.PENDING

    def read(self, key: t.Key) -> Optional[t.Value]:
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

        if not version:
            self.returning[key] = None
            return None

        versionkey, _ = util.decode_key_with_ts(version.key)

        if versionkey != key or version.isdeleted:
            self.returning[key] = None
            return None

        self.returning[key] = version.value
        return version.value

    def write(self, key: t.Key, value: t.Value = bytes(), meta: int = 0):
        """add a pending write"""

        self.writes[key] = storage.Entry(key=key, value=value, meta=meta)

    def isreadonly(self) -> bool:
        """helper"""

        return not self.writes

    def commit(self) -> Transaction:
        """
        dont incur any overhead with oracle if no writes to process.
        else, get a commit ts from oracle and apply to all writes then ship
        over to db to persist
        """

        if not self.writes:
            self.status = TransactionStatus.NOOP
            return self

        with self.db.oracle.write_lock:
            return self._commit()

    def _commit(self) -> Transaction:
        """we have writes, commit transaction"""

        try:
            commit_ts = self.db.oracle.commit_request(self)
        except err.Abort as exc:
            self.status = TransactionStatus.ABORTED
            raise exc

        self.commit_ts = commit_ts
        writes = []

        for key, write in self.writes.items():
            key_with_ts = util.encode_key_with_ts(key=key, ts=commit_ts)
            new_entry = storage.Entry(
                key=key_with_ts, value=write.value, meta=write.meta
            )
            writes.append(new_entry)

        self.db.write(writes)
        self.status = TransactionStatus.COMMITTED
        return self
