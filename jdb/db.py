from .entry import Entry
from .errors import NotFound
from .memtable import Memtable


class DB:
    def __init__(self, max_table_size: int = 128 << 20):
        self._memtable = Memtable(max_size=max_table_size)

    def put(self, key: bytes, value: bytes) -> None:
        entry = Entry(key=key, value=value)
        self._memtable.insert(entry)

    def get(self, key: bytes) -> bytes:
        head = self._memtable.find(key)

        if not head or head.isdeleted:
            raise NotFound()

        return head.value

    def delete(self, key: bytes):
        entry = Entry(key=key, meta=Entry.TOMBSTONE)
        return self._memtable.insert(entry)
