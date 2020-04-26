from datetime import datetime, timezone
from typing import Tuple
from collections import OrderedDict
from uuid import uuid4 as uuid
from xxhash import xxh32_intdigest
from jdb.types import ID, Key, Timestamp
from jdb.const import MAX_UINT_64


def id_from_str(string: str) -> ID:
    """"convert hex str to int"""

    return ID(string, 16)


def id_to_str(ident: ID) -> str:
    """"convert int to hex str"""

    return format(ident, "x")


def gen_id() -> ID:
    """random hash"""

    return xxh32_intdigest(uuid().bytes)


def encode_key_with_ts(key: Key, ts: Timestamp) -> Key:
    """append ts as last 8 bytes of key"""

    encoded_ts = (MAX_UINT_64 - ts).to_bytes(8, byteorder="big")
    return key + encoded_ts


def decode_key_with_ts(key_with_ts: Key) -> Tuple[Key, Timestamp]:
    """parse out ts"""

    key = key_with_ts[:-8]
    ts = MAX_UINT_64 - int.from_bytes(key_with_ts[-8:], byteorder="big")
    return (key, ts)


def now_ms() -> int:
    """ms since epoch"""

    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def byteify_keys(obj: OrderedDict) -> OrderedDict:
    return OrderedDict({k.encode(): v for k, v in obj.items()})
