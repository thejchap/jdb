from pytest import fixture, mark, raises
from jdb.db import DB
from jdb.jql import JQL
from jdb.entry import Entry
from jdb.errors import TableOverflow, Abort
from jdb.transaction import Transaction
from jdb.avltree import AVLTree
from jdb.util import encode_key_with_ts, decode_key_with_ts


@fixture
def db() -> DB:
    return DB()


@fixture
def jql(db: DB):
    return JQL(db=db)


@fixture
def tree():
    def comparator(i: int, j: int):
        if i == j:
            return 0
        elif i < j:
            return -1

        return 1

    return AVLTree[int](comparator=comparator)


@mark.parametrize("key,value,meta", [(b"foo", b"world", 0), (b"hello", b"bar", 1)])
def test_encode_decode(key, value, meta):
    entry = Entry(key=key, value=value, meta=meta)
    encoded = entry.encode()
    assert Entry.decode(encoded) == entry


def test_overflow():
    smalldb = DB(max_table_size=256, compression=None)
    key = bytes(bytearray(128))
    value = b""
    smalldb.put(key, value)

    with raises(TableOverflow):
        smalldb.put(key, value)


def test_compression(db):
    value = ("hello " * 1000 + "world " * 1000).encode("utf-8")
    key = b"hello"
    db.put(key, value)

    assert db.get(key) == value


def test_ssi(db):
    db.put(b"a", b"b")

    t1 = Transaction(db)
    t2 = Transaction(db)
    t3 = Transaction(db)

    t1.write(b"a", b"z")
    t2.read(b"a")
    t2.write(b"a", b"y")

    t3.write(b"c", b"d")
    t3.read(b"c")

    t1.commit()

    with raises(Abort):
        t2.commit()

    t3.commit()

    assert t1.read_ts == 1
    assert t2.read_ts == 1
    assert t3.read_ts == 1
    assert t1.commit_ts == 2
    assert t3.commit_ts == 3


def test_basic(tree: AVLTree):
    tree.insert(1)
    tree.insert(2)
    tree.insert(3)
    tree.insert(4)
    tree.insert(5)
    tree.insert(6)

    assert tree.search(3) == 3
    assert not tree.search(7)


def test_parse_put(jql: JQL, db: DB):
    statement = "put hello world;"
    _, txn = jql.call(statement)

    assert txn
    assert txn.writes[b"hello"].value == b"world"


def test_parse_get(jql: JQL, db: DB):
    db.put(b"hello", b"world")
    statement = "get hello;"
    val, txn = jql.call(statement)

    assert not txn
    assert val == "world"


def test_parse_transaction(jql: JQL):
    statement = "begin transaction\nput a b\nput c d\nend transaction;"
    _, txn = jql.call(statement)

    assert txn
    assert txn.writes[b"a"].value == b"b"
    assert txn.writes[b"c"].value == b"d"


def test_parse_transaction_with_read(jql: JQL):
    statement = "begin transaction\nput a b\nget a\nend transaction;"
    _, txn = jql.call(statement)

    assert txn
    assert txn.writes[b"a"].value == b"b"
    assert b"a" not in txn.reads


def test_key_with_ts():
    key_with_ts = encode_key_with_ts(b"hello", 100)
    key, ts = decode_key_with_ts(key_with_ts)

    assert key == b"hello"
    assert ts == 100
