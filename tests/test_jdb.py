from pytest import fixture
from jdb import Jdb, Entry


@fixture
def db() -> Jdb:
    return Jdb()


def test_put_and_get_basic(db):
    db.put(b"hello", b"world")
    assert db.get(b"hello") == b"world"


def test_delete_basic(db):
    db.put(b"hello", b"world")
    db.delete(b"hello")

    assert not db.get(b"hello")


def test_encode_decode():
    entry = Entry(key=b"foo", value=b"world")

    encoded = entry.encode()
    assert Entry.decode(encoded) == entry
