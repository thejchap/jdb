from typing import Optional, List
from contextlib import contextmanager
from jdb import (
    oracle as orc,
    entry as ent,
    memtable as mem,
    compression as cmp,
    const,
    types,
    transaction as txn,
)


class DB:
    def __init__(
        self,
        max_table_size: int = 128 << 20,
        compression: Optional[cmp.CompressionType] = cmp.CompressionType.LZ4,
    ):
        self.oracle = orc.Oracle()
        self.memtable = mem.Memtable(
            max_size=max_table_size, compression=cmp.Compression(compression)
        )

    def get(self, key: bytes) -> bytes:
        with self.transaction() as transaction:
            return transaction.read(key=key)

    def put(self, key: types.Key, value: types.Value):
        with self.transaction() as transaction:
            transaction.write(key=key, value=value)

    def delete(self, key: bytes):
        with self.transaction() as transaction:
            transaction.write(key=key, meta=const.BIT_TOMBSTONE)

    def write(self, entries: List[ent.Entry]):
        for entry in entries:
            self.memtable.insert(entry)

    def read(self, key: types.Key) -> Optional[ent.Entry]:
        return self.memtable.find(key)

    @contextmanager
    def transaction(self):
        transaction = txn.Transaction(db=self)
        yield transaction
        transaction.commit()
