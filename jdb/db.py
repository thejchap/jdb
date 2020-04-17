from typing import Optional
from .oracle import Oracle
from .entry import Entry
from .errors import NotFound
from .memtable import Memtable
from .compression import CompressionType, Compression


class DB:
    def __init__(
        self,
        max_table_size: int = 128 << 20,
        compression: Optional[CompressionType] = CompressionType.LZ4,
    ):
        self.oracle = Oracle()
        self._memtable = Memtable(
            max_size=max_table_size, compression=Compression(compression)
        )

    def put(self, key: bytes, value: bytes) -> None:
        entry = Entry(key=key, value=value)
        return self.append(entry)

    def get(self, key: bytes) -> bytes:
        head = self._memtable.find(key)

        if not head or head.isdeleted:
            raise NotFound()

        return head.value

    def append(self, entry: Entry):
        self._memtable.insert(entry)

    def delete(self, key: bytes):
        entry = Entry(key=key, meta=Entry.TOMBSTONE)
        return self.append(entry)
