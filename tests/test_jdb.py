# pylint:disable=redefined-outer-name

from pytest import fixture, mark, raises
from freezegun import freeze_time
from jdb import (
    db,
    jql,
    entry as ent,
    errors as err,
    transaction as txn,
    avltree as avl,
    util,
    node as nde,
    hlc,
    crdt,
)


@fixture
def parser(node: nde.Node):
    """parser test subject"""

    return jql.JQL(node=node)


@fixture
def tree():
    """index test subject"""

    return avl.AVLTree[int]()


def test_basic():
    database = db.DB()
    database.put(b"a", b"hello")
    database.put(b"b", b"world")

    val1 = database.get(b"a")
    val2 = database.get(b"b")

    assert val1 == b"hello"
    assert val2 == b"world"


def test_basic_2():
    database = db.DB()
    database.put(b"hello", b"world")
    database.put(b"hello1", b"world1")
    database.put(b"hello2", b"world2")

    val = database.get(b"hello2")

    assert val == b"world2"


@mark.parametrize("key,value,meta", [(b"foo", b"world", 0), (b"hello", b"bar", 1)])
def test_encode_decode(key, value, meta):
    entry = ent.Entry(key=key, value=value, meta=meta)
    encoded = entry.encode()
    assert ent.Entry.decode(encoded) == entry


def test_overflow():
    smalldb = db.DB(max_table_size=256, compression=None)
    key = bytes(bytearray(128))
    value = b""
    smalldb.put(key, value)

    with raises(err.TableOverflow):
        smalldb.put(key, value)


def test_compression():
    database = db.DB()
    value = ("hello " * 1000 + "world " * 1000).encode("utf-8")
    key = b"hello"
    database.put(key, value)

    assert database.get(key) == value


def test_ssi():
    database = db.DB()
    database.put(b"a", b"b")

    txn1 = txn.Transaction(database)
    txn2 = txn.Transaction(database)
    txn3 = txn.Transaction(database)

    txn1.write(b"a", b"z")
    assert txn2.read(b"a") == b"b"
    txn2.write(b"a", b"y")

    txn3.write(b"c", b"d")
    txn3.read(b"c")

    txn1.commit()

    with raises(err.Abort):
        txn2.commit()

    txn3.commit()

    assert txn1.read_ts == 1
    assert txn2.read_ts == 1
    assert txn3.read_ts == 1
    assert txn1.commit_ts == 2
    assert txn3.commit_ts == 3


def test_avl(tree: avl.AVLTree):
    tree.insert(1)
    tree.insert(2)
    tree.insert(3)
    tree.insert(4)
    tree.insert(5)
    tree.insert(6)

    assert tree.search(3) == 3
    assert not tree.search(7)


def test_avl_near(tree: avl.AVLTree):
    tree.insert(3)
    tree.insert(4)
    tree.insert(1)

    assert tree.search(2, gte=True) == 3


def test_avl_near_2(tree: avl.AVLTree):
    tree.insert(2)
    tree.insert(1)
    tree.insert(5)

    assert tree.search(4, gte=True) == 5


def test_avl_near_3(tree: avl.AVLTree):
    tree.insert(5)
    tree.insert(2)
    tree.insert(1)
    tree.insert(3)

    assert tree.search(3, gte=True) == 3


def test_parse_put():
    parser = jql.JQL(node=nde.Node())
    statement = "put hello world;"
    _, txn = parser.call(statement)

    assert txn
    assert txn.writes[b"hello"].value == b"world"


def test_parse_get():
    node = nde.Node()
    parser = jql.JQL(node)
    database = node.store
    database.put(b"hello", b"world")
    statement = "get hello;"
    val, txn1 = parser.call(statement)

    assert not txn1
    assert val == "world"


def test_parse_transaction():
    parser = jql.JQL(node=nde.Node())
    statement = "begin\nput a b\nput c d\nend;"
    _, txn1 = parser.call(statement)

    assert txn1
    assert txn1.writes[b"a"].value == b"b"
    assert txn1.writes[b"c"].value == b"d"


def test_parse_transaction_with_read():
    parser = jql.JQL(node=nde.Node())
    statement = "begin\nput a b\nget a\nend;"
    _, txn1 = parser.call(statement)

    assert txn1
    assert txn1.writes[b"a"].value == b"b"
    assert b"a" not in txn1.reads


def test_key_with_ts():
    key_with_ts = util.encode_key_with_ts(b"hello", 100)
    key, ts = util.decode_key_with_ts(key_with_ts)

    assert key == b"hello"
    assert ts == 100


def test_peer_merge_basic():
    global_clock = hlc.HLC()
    cs1 = crdt.LWWRegister(replica_id=1)
    cs2 = crdt.LWWRegister(replica_id=2)
    cs1.clock = global_clock
    cs2.clock = global_clock
    cs1.add(b"a")
    cs2.remove(b"a")
    cs1.add(b"b")
    cs1.add(b"d")
    cs2.add(b"c")
    cs2.remove(b"d")
    merged = dict(cs1.merge(cs2))

    assert b"b" in merged
    assert b"c" in merged
    assert b"a" not in merged
    assert b"d" not in merged


@freeze_time("1970-01-01")
def test_peer_merge_concurrent():
    cs1 = crdt.LWWRegister(replica_id=1)
    cs2 = crdt.LWWRegister(replica_id=2)
    cs1.remove(b"a")
    cs2.add(b"a")
    merged = cs1.merge(cs2)
    merge_dict = dict(merged)

    assert b"a" in merge_dict


def test_hlc():
    clock = hlc.HLC()
    clock.incr()
    clock.incr()
    clock.incr()
    ts1 = clock.incr()
    ts1int = int(ts1)
    ts2 = hlc.HLCTimestamp.from_int(ts1int)

    assert ts2.ts == ts1.ts
    assert ts2.count == ts1.count
