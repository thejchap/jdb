from typing import Optional
from contextlib import contextmanager
from enum import Enum
from lz4f import (
    compressFrame as lz4f_compress,
    decompressFrame as lz4f_decompress,
    createDecompContext as lz4f_create_dctx,
    freeDecompContext as lz4f_free_dctx,
)
from snappy import (
    compress as snappy_compress,
    decompress as snappy_decompress,
)


class CompressionType(Enum):
    LZ4 = 1
    SNAPPY = 2


class Compression:
    def __init__(self, compression_type: Optional[CompressionType]):
        self._compression_type = compression_type

    @property
    def isenabled(self) -> bool:
        return bool(self._compression_type)

    def compress(self, raw: bytes) -> bytes:
        compressed = raw

        if self._compression_type == CompressionType.LZ4:
            compressed = lz4f_compress(raw)
        elif self._compression_type == CompressionType.SNAPPY:
            compressed = snappy_compress(raw)

        return compressed

    def decompress(self, compressed: bytes) -> bytes:
        raw = compressed

        if self._compression_type == CompressionType.LZ4:
            with self._lz4f_dctx() as dctx:
                raw = lz4f_decompress(compressed, dctx)["decomp"]
        elif self._compression_type == CompressionType.SNAPPY:
            raw = snappy_decompress(compressed)

        return raw

    @contextmanager
    def _lz4f_dctx(self):
        dctx = lz4f_create_dctx()

        try:
            yield dctx
        except Exception as err:
            lz4f_free_dctx(dctx)

            raise err
