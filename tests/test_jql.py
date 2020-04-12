from pytest import fixture
from jdb.jql import JQL
from jdb.db import DB


@fixture
def db():
    return DB()


@fixture
def jql(db: DB):
    return JQL(db=db)


def test_parse_put(jql: JQL, db: DB):
    statement = "put hello world"
    _, txn = jql.call(statement)

    assert txn
    assert txn.entries[0].key == "hello"
    assert txn.entries[0].value == "world"


def test_parse_get(jql: JQL, db: DB):
    db.put(b"hello", b"world")
    statement = "get hello"
    val, txn = jql.call(statement)

    assert not txn
    assert val == "world"


def test_parse_transaction(jql: JQL):
    statement = "begin transaction\nput a b\nput c d\nend transaction"
    _, txn = jql.call(statement)

    assert txn
    assert txn.entries[0].key == "a"
    assert txn.entries[0].value == "b"
    assert txn.entries[1].key == "c"
    assert txn.entries[1].value == "d"


def test_parse_transaction_with_read(jql: JQL):
    statement = "begin transaction\nput a b\nget a\nend transaction"
    _, txn = jql.call(statement)

    assert txn
    assert txn.entries[0].key == "a"
    assert txn.entries[0].value == "b"
    assert txn.reads[0].key == "a"
