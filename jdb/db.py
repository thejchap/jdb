from typing import Optional, List
from contextlib import contextmanager
from jdb.oracle import Oracle
from jdb.entry import Entry
from jdb.memtable import Memtable
from jdb.compression import CompressionType, Compression
from jdb.const import BIT_TOMBSTONE
from jdb.types import Key, Value
from jdb.transaction import Transaction


class DB:
    def __init__(
        self,
        max_table_size: int = 128 << 20,
        compression: Optional[CompressionType] = CompressionType.LZ4,
    ):
        self.oracle = Oracle()
        self.memtable = Memtable(
            max_size=max_table_size, compression=Compression(compression)
        )

    def get(self, key: bytes) -> bytes:
        with self.transaction() as txn:
            return txn.read(key=key)

    def put(self, key: Key, value: Value):
        with self.transaction() as txn:
            txn.write(key=key, value=value)

    def delete(self, key: bytes):
        with self.transaction() as txn:
            txn.write(key=key, meta=BIT_TOMBSTONE)

    def write(self, entries: List[Entry]):
        for entry in entries:
            self.memtable.insert(entry)

    def read(self, key: Key) -> Optional[Entry]:
        return self.memtable.find(key)

    @contextmanager
    def transaction(self):
        txn = Transaction(db=self)
        yield txn
        txn.commit()
