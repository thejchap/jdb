from pytest import fixture, mark, raises
from jdb.db import DB
from jdb.entry import Entry
from jdb.errors import TableOverflow, NotFound, Abort
from jdb.transaction import Transaction, Read


@fixture
def db() -> DB:
    return DB()


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
    smalldb = DB(max_table_size=256, compression=None)
    smalldb.put(bytearray(128), bytearray(0))

    with raises(TableOverflow):
        smalldb.put(bytearray(128), bytearray(0))


def test_compression(db):
    value = ("hello " * 1000 + "world " * 1000).encode("utf-8")
    key = b"hello"
    db.put(key, value)

    assert db.get(key) == value


def test_ssi(db):
    t1 = Transaction(db)
    t2 = Transaction(db)
    t3 = Transaction(db)

    t1.writes.append(Entry(key=b"a", value=b"b"))
    t2.reads.append(Read(key=b"a"))
    t3.reads.append(Read(key=b"c"))
    t3.writes.append(Entry(key=b"c", value=b"d"))

    t1.commit()

    with raises(Abort):
        t2.commit()

    t3.commit()

    assert t1.read_ts == 0
    assert t2.read_ts == 0
    assert t3.read_ts == 0
    assert t1.commit_ts == 1
    assert t3.commit_ts == 2
