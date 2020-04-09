from jdb.jql import Grammar


def test_grammar():
    res = Grammar.parse("PUT hello world;")

    assert res["key"] == "hello"
    assert res["value"] == "world"
    assert res["operation"] == "PUT"
