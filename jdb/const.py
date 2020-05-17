import re

BEGIN = "BEGIN"
END = "END"
PUT = "PUT"
DELETE = "DELETE"
GET = "GET"
INFO = "INFO"
TERMINATOR = ";"
KEY = "key"
VALUE = "value"
TXN = "txn"
OK = "OK"
SYNTAX_ERR = "SYNTAX ERR"
ABORTED = "ABORTED"
COMMITTED = "COMMITTED"
PENDING = "PENDING"
MAX_UINT_64 = 2 ** 64 - 1
MAX_UINT_32 = 2 ** 32 - 1
BIT_TOMBSTONE = 1 << 0
MAGLEV_OFFSET_SEED = 2 << 30
MAGLEV_SKIP_SEED = 2 << 31

# /table/pkey
REQ_KEY_REGEX = re.compile(r"^\/([A-Za-z0-9]+)\/([A-Za-z0-9]+)$")
