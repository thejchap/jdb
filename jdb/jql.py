from typing import Callable, Tuple, Optional
import json
from pyparsing import (
    CaselessKeyword,
    Word,
    alphanums,
    ParseResults,
    OneOrMore,
    Literal,
    Combine,
)
import jdb.routing as rte
import jdb.const as k
import jdb.node as nde

Result = Tuple[Optional[str], Optional[bool]]


def _do_statement(node: nde.Node, tokens: ParseResults) -> Result:
    """entrypoint"""

    if len(tokens) == 1 and isinstance(tokens[0], str) and tokens[0] == k.INFO:
        return json.dumps(dict(node)), None

    if "txn" in tokens:
        return tokens.txn(node)

    return _do_batch_request(tokens)(node)


def _do_batch_request(tokens: ParseResults) -> Callable[[nde.Node], Result]:
    """return a fn to execute a transaction"""

    def wrapper(node: nde.Node):
        req = rte.BatchRequest(requests=tokens)
        ret = node.router.request(req)

        return k.OK, ret

    return wrapper


def _do_put(tokens: ParseResults) -> rte.PutRequest:
    """build a txn entry from tokens"""

    return rte.PutRequest(key=tokens.key.encode(), value=tokens.value.encode())


def _do_get(tokens: ParseResults) -> rte.GetRequest:
    """just return the key"""

    return rte.GetRequest(key=tokens.key.encode())


def _do_delete(tokens: ParseResults) -> rte.DeleteRequest:
    """build a txn entry from tokens"""

    return rte.DeleteRequest(key=tokens.key.encode())


class JQL:
    """this whole thing is a little wack. but yea - simple parser for cli commands"""

    _key = Combine(Literal("/") + Word(alphanums) + Literal("/") + Word(alphanums))
    _put = (
        CaselessKeyword(k.PUT).suppress()
        + _key.setResultsName(k.KEY)
        + Word(alphanums).setResultsName(k.VALUE)
    ).addParseAction(_do_put)
    _get = (
        CaselessKeyword(k.GET).suppress() + _key.setResultsName(k.KEY)
    ).addParseAction(_do_get)
    _delete = (
        CaselessKeyword(k.DELETE).suppress() + _key.setResultsName(k.KEY)
    ).addParseAction(_do_delete)
    _info = CaselessKeyword(k.INFO)
    _operation = _put | _delete | _get
    _transaction = (
        (
            CaselessKeyword(k.BEGIN).suppress()
            + OneOrMore(_operation)
            + CaselessKeyword(k.END).suppress()
        )
        .addParseAction(_do_batch_request)
        .setResultsName(k.TXN)
    )

    _statement = (_operation | _transaction | _info) + Literal(k.TERMINATOR).suppress()

    def __init__(self, node: nde.Node):
        self._node = node
        self._statement.setParseAction(self._with_db(_do_statement))

    def call(self, statement: str) -> Result:
        """main entrypoint"""

        return self._statement.parseString(statement, parseAll=True)[0]

    def _with_db(self, func: Callable) -> Callable:
        """pass node into actions"""

        def wrapped(tokens: ParseResults):
            return func(self._node, tokens)

        return wrapped
