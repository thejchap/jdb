from jdb.errors import Abort
from jdb.const import MAX_UINT_64


class Oracle:
    """
    transaction status oracle.
    enforce isolation levels and maintain ordering of transactions.
    transactions aren't threadsafe but the operations in this class must be
    """

    def __init__(self):
        self._next_ts = 1
        self._commits = {}

    def __next__(self) -> int:
        res = self._next_ts
        self._next_ts += 1
        return res

    def __iter__(self):
        return self

    def read_ts(self) -> int:
        """
        if a transaction gets a commit timestamp of 1
        then its snapshot of the db includes everything that occurred until 0
        """

        return self._next_ts - 1

    def commit_request(self, txn) -> int:
        """
        per ssi - abort transaction if there are any writes that have occurred since
        this transaction started that affect keys read by this transaction, then keep
        track of this transaction's writes for other transactions to do the same
        """

        for key in txn.reads:
            last_commit = self._commits.get(key)

            if last_commit and last_commit > txn.read_ts:
                raise Abort()

        ts = next(iter(self))

        if ts == MAX_UINT_64:
            raise OverflowError()

        for key in txn.writes.keys():
            self._commits[key] = ts

        return ts
