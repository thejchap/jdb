from datetime import datetime, timezone
from typing import Tuple
from uuid import uuid4 as uuid
from xxhash import xxh32_intdigest
from jdb.types import ID, Key, Timestamp
from jdb.const import MAX_UINT_64


def id_from_str(string: str) -> ID:
    return ID(string, 16)


def id_to_str(ident: ID) -> str:
    return format(ident, "x")


def gen_id() -> ID:
    return xxh32_intdigest(uuid().bytes)


def encode_key_with_ts(key: Key, ts: Timestamp) -> Key:
    encoded_ts = (MAX_UINT_64 - ts).to_bytes(8, byteorder="big")
    return key + encoded_ts


def decode_key_with_ts(key_with_ts: Key) -> Tuple[Key, Timestamp]:
    key = key_with_ts[:-8]
    ts = MAX_UINT_64 - int.from_bytes(key_with_ts[-8:], byteorder="big")
    return (key, ts)


def now_ms() -> int:
    """ms since epoch"""

    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)
