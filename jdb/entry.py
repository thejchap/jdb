from __future__ import annotations
from typing import Optional
from binascii import crc32
from dataclasses import dataclass
import uvarint
from jdb import errors as err, compression as cmp, const, types


@dataclass
class Entry:
    """represents a unit of storage in the db/log"""

    key: bytes
    value: bytes = bytes()
    meta: int = 0

    @classmethod
    def decode(cls, buf: bytes, compression: Optional[cmp.Compression] = None) -> Entry:
        """
        1. decode header
        2. use header metadata to decode body
        3. verify checksum, raise if mismatch
        4. return object
        """

        decoded = uvarint.cut(4, buf)
        body = decoded.rest
        _, meta, keylen, valuelen = decoded.integers
        key = bytes(body[0:keylen])
        value = bytes(body[keylen : keylen + valuelen])

        checksum_bytes = body[keylen + valuelen :]
        checksum = uvarint.decode(checksum_bytes).integer
        header = cls._encode_header(key=key, value=value, meta=meta)
        check = crc32(header)
        check = crc32(key, check)
        check = crc32(value, check)

        if checksum != check:
            raise err.ChecksumMismatch()

        if compression and compression.isenabled:
            key = compression.decompress(key)
            value = compression.decompress(value)

        return Entry(key=key, value=value, meta=meta)

    @property
    def isdeleted(self) -> bool:
        """return true if tombstone bit is set"""

        return self.meta & const.BIT_TOMBSTONE == 1

    def encode(self, compression: Optional[cmp.Compression] = None) -> bytes:
        """
        byte array representation of log entry.
        append CRC32 checksum of header and k/v
        -----------------------------------------------------------------------
        | block size | meta | key length | value length | key | value | crc32 |
        -----------------------------------------------------------------------
        """

        key, value, meta = self.key, self.value, self.meta

        if compression and compression.isenabled:
            key = compression.compress(key)
            value = compression.compress(value)

        header = self._encode_header(key=key, value=value, meta=meta)
        checksum = crc32(header)
        encoded = bytearray(header)
        checksum = crc32(key, checksum)
        encoded += key
        checksum = crc32(value, checksum)
        encoded += value
        encoded += uvarint.encode(checksum)
        block_size = uvarint.encode(len(encoded))

        return bytes([*block_size, *encoded])

    @classmethod
    def _encode_header(cls, key: types.Key, value: types.Value, meta: int) -> bytes:
        """
        byte array representation of header fields/metadata
        ------------------------------------
        | meta | key length | value length |
        ------------------------------------
        """

        header_fields = [len(key), len(value)]
        header = bytearray([meta])

        for val in header_fields:
            header += uvarint.encode(val)

        return header
