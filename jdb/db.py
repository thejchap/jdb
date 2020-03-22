from typing import Optional, Generator
from math import ceil
import uvarint
from .entry import Entry


class Options:
    max_table_size: Optional[int] = 64 << 20


class Db:
    _log: bytearray = bytearray()

    def __init__(self, options: Options = Options()):
        self.opts = options

    def put(self, key: bytes, value: bytes) -> bool:
        entry = Entry(key=key, value=value)
        self._log += entry.encode()
        return True

    def get(self, key: bytes) -> Optional[bytes]:
        stack = list([x for x in self.scan() if x.key == key])

        if not len(stack) or stack[-1].isdeleted:
            return None

        return stack[-1].value

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
