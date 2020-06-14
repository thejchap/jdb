from typing import Generator, Tuple, Optional
from math import ceil
import uvarint
from jdb.storage import entry as ent, avltree as avl, compression as cmp
from jdb import errors as err, types


class Memtable:
    """in memory representation of db"""

    def __init__(self, max_size: int, compression: cmp.Compression):
        self.max_size = max_size
        self._compression = compression
        self._arena = bytearray()
        self._entries_count = 0
        self._offset = 0
        self._index = avl.AVLTree()

    def put(self, entry: ent.Entry) -> None:
        """append an entry to the log"""

        encoded = entry.encode(compression=self._compression)
        size = len(encoded)

        if self.size() + size > self.max_size:
            raise err.TableOverflow()

        self._index.insert((entry.key, self._offset))
        self._arena += encoded
        self._entries_count += 1
        self._offset += size

    def get(self, key: types.Key) -> Optional[ent.Entry]:
        """find key and pointer in index, lookup value"""

        val = self._find_near(key)

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

    def scan(self) -> Generator[ent.Entry, None, None]:
        """scan through log"""

        offset = 0

        while offset < len(self._arena):
            entry, bytes_read = self._decode_at_offset(offset)
            yield entry
            offset = offset + bytes_read

    def _find_near(self, key: types.Key) -> Optional[types.IndexEntry]:
        """find the closest version of this key"""

        return self._index.search((key, 0), gte=True)

    def _decode_at_offset(self, offset: types.Offset) -> Tuple[ent.Entry, int]:
        """
        given an offset, return the entry starting there
        and the byte length of the entry
        """

        block_size = uvarint.cut(1, self._arena[offset:]).integers[0]
        block_end = offset + block_size + ceil(block_size.bit_length() / 8)
        bytes_read = block_end - offset
        chunk = self._arena[offset:block_end]
        decoded = ent.Entry.decode(chunk, compression=self._compression)

        return (decoded, bytes_read)
