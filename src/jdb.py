from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
import uvarint


@dataclass
class Entry:
    TOMBSTONE = 1 << 0

    key: bytes
    value: bytes = bytes()
    meta: int = 0

    @property
    def isdeleted(self) -> bool:
        return self.meta & self.TOMBSTONE == 1

    def encode(self) -> bytes:
        header_fields = [len(self.key), len(self.value)]
        header = bytearray([self.meta])

        for val in header_fields:
            header += uvarint.encode(val)

        encoded = bytearray(header)
        encoded += self.key
        encoded += self.value

        return bytes(encoded)

    @classmethod
    def decode(cls, buf: bytes) -> Entry:
        decoded = uvarint.cut(3, buf)
        body = decoded.rest
        meta, keylen, valuelen = decoded.integers
        key = body[0:keylen]
        value = body[keylen : keylen + valuelen]

        return Entry(key=key, value=value, meta=meta)


class Options:
    max_table_size: Optional[int] = 64 << 20


class Jdb:
    _log: List[Entry] = []

    def __init__(self, options: Options = Options()):
        self.opts = options

    def put(self, key: bytes, value: bytes) -> bool:
        entry = Entry(key=key, value=value)
        self._log.append(entry)
        return True

    def get(self, key: bytes) -> Optional[bytes]:
        entry = next(x for x in reversed(self._log) if x.key == key)

        if entry and not entry.isdeleted:
            return entry.value

        return None

    def delete(self, key: bytes):
        entry = Entry(key=key, meta=Entry.TOMBSTONE)
        self._log.append(entry)
