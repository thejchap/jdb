from typing import Optional, List
from contextlib import contextmanager
from jdb.storage import (
    oracle as orc,
    entry as ent,
    memtable as mem,
    compression as cmp,
    transaction as txn,
)
from jdb import (
    const,
    types,
)


class DB:
    """main db/storage entry point"""

    def __init__(
        self,
        max_table_size: int = 1024 << 20,
        compression: Optional[cmp.CompressionType] = cmp.CompressionType.SNAPPY,
    ):
        self.oracle = orc.Oracle()
        self.memtable = mem.Memtable(
            max_size=max_table_size, compression=cmp.Compression(compression)
        )

    def get(self, key: bytes) -> bytes:
        """main get API if interfacing with db class directly"""

        with self.transaction() as transaction:
            return transaction.read(key=key)

    def put(self, key: types.Key, value: types.Value):
        """main put API if interfacing with db class directly"""

        with self.transaction() as transaction:
            transaction.write(key=key, value=value)

    def delete(self, key: bytes):
        """main delete API if interfacing with db class directly"""

        with self.transaction() as transaction:
            transaction.write(key=key, meta=const.BIT_TOMBSTONE)

    def write(self, entries: List[ent.Entry]):
        """called by transactions to submit their writes"""

        for entry in entries:
            self.memtable.put(entry)

    def read(self, key: types.Key) -> Optional[ent.Entry]:
        """called by transactions to read from the db"""

        return self.memtable.get(key)

    @contextmanager
    def transaction(self):
        """create/yield/commit transaction"""

        transaction = txn.Transaction(db=self)
        yield transaction
        transaction.commit()
