from pytest import fixture
from jdb.jql import JQL


@fixture
def jql():
    return JQL()


def test_parse(jql: JQL):
    res = jql.parse("PUT hello world;")

    assert res["key"] == "hello"
    assert res["value"] == "world"
    assert res["op"] == "PUT"
