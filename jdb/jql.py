from pyparsing import CaselessKeyword, Word, alphanums, Literal

# reserved tokens
PUT = "PUT"
DELETE = "DELETE"
GET = "GET"
EXIT = "EXIT"
TERMINATOR = ";"

# results
OP = "op"
KEY = "key"
VALUE = "value"


class JQL:
    _put = (
        CaselessKeyword(PUT).setResultsName(OP)
        + Word(alphanums).setResultsName(KEY)
        + Word(alphanums).setResultsName(VALUE)
    )

    _get = CaselessKeyword(GET).setResultsName(OP) + Word(alphanums).setResultsName(KEY)
    _xit = CaselessKeyword(EXIT).setResultsName(OP)

    _delete = CaselessKeyword(DELETE).setResultsName(OP) + Word(
        alphanums
    ).setResultsName(KEY)

    _statement = (_put | _get | _delete | _xit) + Literal(TERMINATOR).suppress()

    def parse(self, txt: str):
        return self._statement.parseString(txt, parseAll=True)
