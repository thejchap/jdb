from pytest import fixture, mark
from jdb.db import Db
from jdb.entry import Entry


@fixture
def db() -> Db:
    return Db()


def test_put_and_get_basic(db):
    db.put(b"hello", b"world")
    assert db.get(b"hello") == b"world"


def test_delete_basic(db):
    db.put(b"hello", b"world")
    db.put(b"foo", b"bar")
    db.put(b"helo", b"world")
    db.delete(b"hello")
    db.delete(b"foo")
    db.delete(b"hel")
    db.put(b"foo", b"baz")

    assert not db.get(b"hello")
    assert not db.get(b"hel")
    assert db.get(b"foo")


@mark.parametrize("key,value,meta", [(b"foo", b"world", 0), (b"hello", b"bar", 1)])
def test_encode_decode(key, value, meta):
    entry = Entry(key=key, value=value, meta=meta)
    encoded = entry.encode()
    assert Entry.decode(encoded) == entry


# TODO
@mark.skip
def test_overflow():
    pass
