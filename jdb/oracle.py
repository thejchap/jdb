from threading import Lock
from jdb import errors as err, const


class Oracle:
    """
    transaction status oracle.
    enforce isolation levels and maintain ordering of transactions.
    transactions aren't threadsafe but the operations in this class must be
    """

    def __init__(self):
        self._next_ts = 1
        self._commits = {}
        self._lock = Lock()
        self.write_lock = Lock()

    def read_ts(self) -> int:
        """
        if a transaction gets a commit timestamp of 1
        then its snapshot of the db includes everything that occurred until 0
        """

        with self._lock:
            return self._next_ts - 1

    def commit_request(self, txn) -> int:
        """
        per ssi - abort transaction if there are any writes that have occurred since
        this transaction started that affect keys read by this transaction, then keep
        track of this transaction's writes for other transactions to do the same.
        threadsafe
        """

        with self._lock:
            return self._commit_request(txn)

    def _commit_request(self, txn) -> int:
        """not threadsafe"""

        for key in txn.reads:
            last_commit = self._commits.get(key)

            if last_commit and last_commit > txn.read_ts:
                raise err.Abort()

        ts = self._next_ts
        self._next_ts += 1

        if ts == const.MAX_UINT_64:
            raise OverflowError()

        for key in txn.writes.keys():
            self._commits[key] = ts

        return ts
