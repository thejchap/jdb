from typing import Generator, Tuple, Optional
from math import ceil
import uvarint
from .entry import Entry
from .errors import TableOverflow
from .avltree import AVLTree
from .compression import Compression
from .types import IndexEntry, Key, Offset


class Memtable:
    """in memory representation of db"""

    def __init__(self, max_size: int, compression: Compression):
        self.max_size = max_size
        self._compression = compression
        self._arena = bytearray()
        self._entries_count = 0
        self._offset = 0
        self._index = AVLTree[IndexEntry](comparison_key=lambda x: x[0])

    def insert(self, entry: Entry) -> None:
        """append an entry to the log"""

        encoded = entry.encode(compression=self._compression)
        size = len(encoded)

        if self.size() + size > self.max_size:
            raise TableOverflow()

        self._index.insert((entry.key, self._offset))
        self._arena += encoded
        self._entries_count += 1
        self._offset += size

    def find(self, key: Key) -> Optional[Entry]:
        """find key and pointer in index, lookup value"""

        val = self._index.search((key, 0))

        if not val:
            return None

        offset = val[1]
        entry, _ = self._decode_at_offset(offset)
        return entry

    def size(self) -> int:
        """byte length of storage"""

        return len(self._arena)

    def entries_count(self) -> int:
        """number of entries in db"""

        return self._entries_count

    def scan(self) -> Generator[Entry, None, None]:
        """scan through log"""

        offset = 0

        while offset < len(self._arena):
            entry, bytes_read = self._decode_at_offset(offset)
            yield entry
            offset = offset + bytes_read

    def _decode_at_offset(self, offset: Offset) -> Tuple[Entry, int]:
        """
        given an offset, return the entry starting there
        and the byte length of the entry
        """

        block_size = uvarint.cut(1, self._arena[offset:]).integers[0]
        block_end = offset + block_size + ceil(block_size.bit_length() / 8)
        bytes_read = block_end - offset
        chunk = self._arena[offset:block_end]
        decoded = Entry.decode(chunk, compression=self._compression)

        return (decoded, bytes_read)
