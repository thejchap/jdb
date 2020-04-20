from sys import argv
from typing import Callable, Tuple, Optional
from pyparsing import CaselessKeyword, Word, alphanums, ParseResults, OneOrMore, Literal
from jdb.db import DB
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
)

Result = Tuple[Optional[str], Optional[Transaction]]


def _do_statement(db: DB, tokens: ParseResults) -> Result:
    if "txn" in tokens:
        return tokens.txn(db)

    if len(tokens) == 1 and isinstance(tokens[0], Key):
        try:
            return (db.get(tokens[0]).decode(), None)
        except NotFound:
            return (None, None)

    return _do_transaction(tokens)(db)


def _do_transaction(tokens: ParseResults) -> Callable[[DB], Result]:
    def wrapper(db: DB):
        txn = Transaction(db=db)

        for tok in tokens:
            if isinstance(tok, Key):
                txn.read(tok)
            else:
                txn.write(tok.key, tok.value, tok.meta)

        return OK, txn.commit()

    return wrapper


def _do_put(tokens: ParseResults) -> Entry:
    return Entry(key=tokens.key.encode(), value=tokens.value.encode())


def _do_get(tokens: ParseResults) -> Key:
    return tokens.key.encode()


def _do_delete(tokens: ParseResults) -> Entry:
    return Entry(key=tokens.key.encode(), meta=BIT_TOMBSTONE)


class JQL:
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

    _statement = (_operation | _transaction) + Literal(TERMINATOR).suppress()

    def __init__(self, db: DB):
        self._db = db
        self._statement.setParseAction(self._with_db(_do_statement))

    def call(self, statement: str) -> Result:
        return self._statement.parseString(statement, parseAll=True)[0]

    def _with_db(self, func: Callable) -> Callable:
        def wrapped(tokens: ParseResults) -> Transaction:
            return func(self._db, tokens)

        return wrapped


def _main():
    jql = JQL(db=DB())
    res = jql.call(argv[1])
    print(res[0])


if __name__ == "__main__":
    _main()
