from typing import Generator, Tuple, Optional
from math import ceil
import uvarint
from .entry import Entry
from .errors import TableOverflow
from .avltree import AVLTree

Key = bytes
Offset = int
IndexEntry = Tuple[Key, Offset]


def _comparator(a: IndexEntry, b: IndexEntry) -> int:
    if a[0] == b[0]:
        return 0
    elif a[0] < b[0]:
        return -1
    return 1


class Memtable:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._arena = bytearray()
        self._entries_count = 0
        self._offset = 0
        self._index = AVLTree[IndexEntry](comparator=_comparator)

    def insert(self, entry: Entry) -> None:
        encoded = entry.encode()
        size = len(encoded)

        if self.size() + size > self.max_size:
            raise TableOverflow()

        self._index.insert((entry.key, self._offset))
        self._arena += encoded
        self._entries_count += 1
        self._offset += size

    def find(self, key: Key) -> Optional[Entry]:
        val = self._index.search((key, 0))

        if not val:
            return None

        offset = val[1]
        entry, _ = self._decode_at_offset(offset)
        return entry

    def size(self) -> int:
        return len(self._arena)

    def entries_count(self) -> int:
        return self._entries_count

    def scan(self) -> Generator[Entry, None, None]:
        offset = 0

        while offset < len(self._arena):
            entry, bytes_read = self._decode_at_offset(offset)
            yield entry
            offset = offset + bytes_read

    def _decode_at_offset(self, offset: Offset) -> Tuple[Entry, int]:
        block_size = uvarint.cut(1, self._arena[offset:]).integers[0]
        block_end = offset + block_size + ceil(block_size.bit_length() / 8)
        bytes_read = block_end - offset
        return (Entry.decode(self._arena[offset:block_end]), bytes_read)
