from typing import Optional
from enum import Enum
from snappy import compress, decompress


class CompressionType(Enum):
    """only snappy supported for now"""

    SNAPPY = 1


class Compression:
    """wrapper for compression. lz4 was being weird so just snappy for now"""

    def __init__(self, compression_type: Optional[CompressionType]):
        self._compression_type = compression_type

    @property
    def isenabled(self) -> bool:
        """did we set one"""

        return bool(self._compression_type)

    def compress(self, raw: bytes) -> bytes:
        """only one type for now"""

        compressed = raw

        if self._compression_type == CompressionType.SNAPPY:
            compressed = compress(raw)

        return compressed

    def decompress(self, compressed: bytes) -> bytes:
        """only one type for now"""

        raw = compressed

        if self._compression_type == CompressionType.SNAPPY:
            raw = decompress(compressed)

        return raw
