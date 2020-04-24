from typing import Callable, Tuple, Optional
import json
from pyparsing import CaselessKeyword, Word, alphanums, ParseResults, OneOrMore, Literal
from jdb.node import Node
from jdb.entry import Entry
from jdb.errors import NotFound
from jdb.transaction import Transaction
from jdb.types import Key
from jdb.const import (
    PUT,
    GET,
    DELETE,
    VALUE,
    OK,
    KEY,
    BEGIN,
    END,
    TXN,
    TERMINATOR,
    BIT_TOMBSTONE,
    INFO,
)

Result = Tuple[Optional[str], Optional[Transaction]]


def _do_statement(node: Node, tokens: ParseResults) -> Result:
    """entrypoint"""

    if len(tokens) == 1 and isinstance(tokens[0], str) and tokens[0] == INFO:
        return json.dumps(dict(node)), None

    if "txn" in tokens:
        return tokens.txn(node.store)

    if len(tokens) == 1 and isinstance(tokens[0], Key):
        try:
            return node.store.get(tokens[0]).decode(), None
        except NotFound:
            return None, None

    return _do_transaction(tokens)(node)


def _do_transaction(tokens: ParseResults) -> Callable[[Node], Result]:
    """return a fn to execute a transaction"""

    def wrapper(node: Node):
        txn = Transaction(db=node.store)

        for tok in tokens:
            if isinstance(tok, Key):
                txn.read(tok)
            else:
                txn.write(tok.key, tok.value, tok.meta)

        return OK, txn.commit()

    return wrapper


def _do_put(tokens: ParseResults) -> Entry:
    """build a txn entry from tokens"""

    return Entry(key=tokens.key.encode(), value=tokens.value.encode())


def _do_get(tokens: ParseResults) -> Key:
    """just return the key"""

    return tokens.key.encode()


def _do_delete(tokens: ParseResults) -> Entry:
    """build a txn entry from tokens"""

    return Entry(key=tokens.key.encode(), meta=BIT_TOMBSTONE)


class JQL:
    """this whole thing is a little wack. but yea - simple parser for cli commands"""

    _put = (
        CaselessKeyword(PUT).suppress()
        + Word(alphanums).setResultsName(KEY)
        + Word(alphanums).setResultsName(VALUE)
    ).addParseAction(_do_put)
    _get = (
        CaselessKeyword(GET).suppress() + Word(alphanums).setResultsName(KEY)
    ).addParseAction(_do_get)
    _delete = (
        CaselessKeyword(DELETE).suppress() + Word(alphanums).setResultsName(KEY)
    ).addParseAction(_do_delete)
    _info = CaselessKeyword(INFO)
    _operation = _put | _delete | _get
    _transaction = (
        (
            CaselessKeyword(BEGIN).suppress()
            + OneOrMore(_operation)
            + CaselessKeyword(END).suppress()
        )
        .addParseAction(_do_transaction)
        .setResultsName(TXN)
    )

    _statement = (_operation | _transaction | _info) + Literal(TERMINATOR).suppress()

    def __init__(self, node: Node):
        self._node = node
        self._statement.setParseAction(self._with_db(_do_statement))

    def call(self, statement: str) -> Result:
        """main entrypoint"""

        return self._statement.parseString(statement, parseAll=True)[0]

    def _with_db(self, func: Callable) -> Callable:
        """pass node into actions"""

        def wrapped(tokens: ParseResults) -> Transaction:
            return func(self._node, tokens)

        return wrapped
