from uuid import uuid4 as uuid
from xxhash import xxh64_intdigest

ID = int


def id_from_str(string: str) -> ID:
    return ID(string, 16)


def id_to_str(ident: ID) -> str:
    return format(ident, "x")


def gen_id() -> ID:
    return xxh64_intdigest(uuid().bytes)
