from pytest import fixture, mark, raises
from jdb.db import Db
from jdb.entry import Entry
from jdb.errors import LogOverflow, NotFound


@fixture
def db() -> Db:
    return Db()


def test_put_and_get_basic(db):
    db.put(b"hello", b"world")
    val = db.get(b"hello")

    assert val == b"world"


def test_delete_basic(db):
    db.put(b"hello", b"world")
    db.put(b"foo", b"bar")
    db.put(b"helo", b"world")
    db.delete(b"hello")
    db.delete(b"foo")
    db.delete(b"hel")
    db.put(b"foo", b"baz")

    with raises(NotFound):
        db.get(b"hello")

    with raises(NotFound):
        db.get(b"hel")

    assert db.get(b"foo")


@mark.parametrize("key,value,meta", [(b"foo", b"world", 0), (b"hello", b"bar", 1)])
def test_encode_decode(key, value, meta):
    entry = Entry(key=key, value=value, meta=meta)
    encoded = entry.encode()
    assert Entry.decode(encoded) == entry


def test_overflow():
    smalldb = Db(max_table_size=256)
    smalldb.put(bytearray(128), bytearray(0))

    with raises(LogOverflow):
        smalldb.put(bytearray(128), bytearray(0))
