# pylint:disable=redefined-outer-name

from pytest import fixture, mark, raises
from freezegun import freeze_time
import jdb.storage as db
import jdb.errors as err
import jdb.jql as jql
import jdb.util as util
import jdb.node as nde
import jdb.hlc as hlc
import jdb.crdt as crdt
import jdb.routing as rte
import jdb.membership as mbr
import jdb.maglev as mag


@fixture
def parser(node: nde.Node):
    """parser test subject"""

    return jql.JQL(node=node)


@fixture
def tree():
    """index test subject"""

    return db.AVLTree()


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


def test_correct_key():
    database = db.DB()
    database.put(b"/world/1", b"hello")

    val = database.get(b"/hello/world")

    assert not val


@mark.parametrize("key,value,meta", [(b"foo", b"world", 0), (b"hello", b"bar", 1)])
def test_encode_decode(key, value, meta):
    entry = db.Entry(key=key, value=value, meta=meta)
    encoded = entry.encode()
    assert db.Entry.decode(encoded) == entry


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

    txn1 = db.Transaction(database)
    txn2 = db.Transaction(database)
    txn3 = db.Transaction(database)

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


def test_avl(tree: db.AVLTree):
    tree.insert((bytes([10]), 0))
    tree.insert((bytes([20]), 0))
    tree.insert((bytes([30]), 0))
    tree.insert((bytes([40]), 0))
    tree.insert((bytes([50]), 0))
    tree.insert((bytes([25]), 0))

    assert tree.root
    assert int.from_bytes(tree.root.key[0], byteorder="big") == 30
    assert tree.root.left
    assert int.from_bytes(tree.root.left.key[0], byteorder="big") == 20
    assert tree.root.left.left
    assert int.from_bytes(tree.root.left.left.key[0], byteorder="big") == 10
    assert tree.root.left.right
    assert int.from_bytes(tree.root.left.right.key[0], byteorder="big") == 25
    assert tree.root.right
    assert int.from_bytes(tree.root.right.key[0], byteorder="big") == 40
    assert tree.root.right.right
    assert int.from_bytes(tree.root.right.right.key[0], byteorder="big") == 50
    assert not tree.search((bytes([70]), 0))


def test_avl_near(tree: db.AVLTree):
    tree.insert((bytes([3]), 0))
    tree.insert((bytes([4]), 0))
    tree.insert((bytes([1]), 0))

    assert tree.search((bytes([2]), 0), gte=True) == (bytes([3]), 0)


def test_avl_near_2(tree: db.AVLTree):
    tree.insert((bytes([2]), 0))
    tree.insert((bytes([1]), 0))
    tree.insert((bytes([5]), 0))

    assert tree.search((bytes([4]), 0), gte=True) == (bytes([5]), 0)


def test_avl_near_3(tree: db.AVLTree):
    tree.insert((bytes([5]), 0))
    tree.insert((bytes([2]), 0))
    tree.insert((bytes([1]), 0))
    tree.insert((bytes([3]), 0))

    assert tree.search((bytes([3]), 0), gte=True) == (bytes([3]), 0)


@mark.skip
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


@mark.skip
def test_parse_transaction():
    parser = jql.JQL(node=nde.Node())
    statement = "begin\nput a b\nput c d\nend;"
    _, txn1 = parser.call(statement)

    assert txn1
    assert txn1.writes[b"a"].value == b"b"
    assert txn1.writes[b"c"].value == b"d"


@mark.skip
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


def test_routing():
    name = "3"
    addr = "0.0.0.3"
    node = nde.Node(name=name, p2p_addr=addr)
    membership = mbr.Membership(node_name=name, node_addr=addr)
    membership.add_peer("1", "0.0.0.1")
    router = rte.Router(membership=membership, node=node)
    req = rte.BatchRequest()
    req.requests.append(rte.PutRequest(key=b"/2/a", value=b"1"))

    router.request(req)


def test_maglev():
    maglev = mag.Maglev({"a", "b", "c"})
    assert maglev.m == 307

    for entry in maglev.table:
        assert entry != -1
