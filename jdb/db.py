from typing import Optional, Generator
from math import ceil
import uvarint
from .entry import Entry
from .errors import NotFound, LogOverflow


class Db:
    def __init__(self, max_table_size: int = 128 << 20):
        self.max_table_size = max_table_size
        self._log = bytearray()

    def put(self, key: bytes, value: bytes) -> bool:
        entry = Entry(key=key, value=value).encode()

        if len(self._log) + len(entry) > self.max_table_size:
            raise LogOverflow()

        self._log += entry
        return True

    def get(self, key: bytes) -> Optional[bytes]:
        stack = reversed([x for x in self.scan() if x.key == key])
        head = next(stack)

        if not head or head.isdeleted:
            raise NotFound()

        return head.value

    def scan(self) -> Generator[Entry, None, None]:
        offset = 0

        while offset < len(self._log):
            block_size = uvarint.cut(1, self._log[offset:]).integers[0]
            block_end = offset + block_size + ceil(block_size.bit_length() / 8)
            yield Entry.decode(self._log[offset:block_end])
            offset = block_end

    def delete(self, key: bytes):
        entry = Entry(key=key, meta=Entry.TOMBSTONE)
        self._log += entry.encode()
