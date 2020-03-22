from __future__ import annotations
import uvarint
from dataclasses import dataclass


@dataclass
class Entry:
    TOMBSTONE = 1 << 0

    key: bytes
    value: bytes = bytes()
    meta: int = 0

    @classmethod
    def decode(cls, buf: bytes) -> Entry:
        "takes a byte array and loads into an Entry object"

        decoded = uvarint.cut(4, buf)
        body = decoded.rest
        _, meta, keylen, valuelen = decoded.integers
        key = bytes(body[0:keylen])
        value = bytes(body[keylen : keylen + valuelen])

        return Entry(key=key, value=value, meta=meta)

    @property
    def isdeleted(self) -> bool:
        """return true if tombstone bit is set"""

        return self.meta & self.TOMBSTONE == 1

    def encode(self) -> bytes:
        """
        byte array representation of log entry

        ---------------------------------------------------------------
        | block size | meta | key length | value length | key | value |
        ---------------------------------------------------------------
        """

        encoded = bytearray(self._encode_header())
        encoded += self.key
        encoded += self.value
        block_size = uvarint.encode(len(encoded))

        return bytes([*block_size, *encoded])

    def _encode_header(self) -> bytes:
        """
        byte array representation of header fields/metadata

        ------------------------------------
        | meta | key length | value length |
        ------------------------------------
        """

        header_fields = [len(self.key), len(self.value)]
        header = bytearray([self.meta])

        for val in header_fields:
            header += uvarint.encode(val)

        return header
