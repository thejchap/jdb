from .errors import Abort


class Oracle:
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
        return self._next_ts - 1

    def commit_request(self, txn) -> int:
        for key in txn.read_set:
            last_commit = self._commits.get(key)

            if last_commit and last_commit > txn.read_ts:
                raise Abort()

        ts = next(iter(self))

        for key in txn.write_set:
            self._commits[key] = ts

        return ts
