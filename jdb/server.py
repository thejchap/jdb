from typing import Dict
from socketserver import TCPServer, StreamRequestHandler
from argparse import ArgumentParser
from pyparsing import ParseException
from structlog import get_logger
from jdb.jql import JQL, SYNTAX_ERR, TERMINATOR
from jdb.db import DB
from jdb.id import ID, id_to_str, gen_id

_LOGGER = get_logger()


class Conn(StreamRequestHandler):
    client_id: ID
    jql: JQL

    def setup(self):
        super().setup()

        self.client_id = gen_id()
        self.jql = JQL(db=self.server.db)
        self.logger = self.server.logger.bind(
            client_id=id_to_str(self.client_id), client_address=self.client_address
        )

    def handle(self):
        statement = ""

        for data in self.rfile:
            raw = data.decode().rstrip()

            if not len(raw):
                break

            statement += f"{raw}\n"
            stripped = statement.rstrip()

            if stripped[-1:] == TERMINATOR:
                self._call(statement)
                statement = ""

    def _call(self, statement: str):
        self.logger.debug("statement", statement=f"{statement!r}")

        try:
            result, txn = self.jql.call(statement=statement)
            self.logger.debug(
                "result", result=result, txnid=(txn.txnid if txn else None)
            )
            self.wfile.write(f"{result}\n".encode())
        except ParseException as err:
            self.logger.err(err)
            self.wfile.write(f"{SYNTAX_ERR}: ln {err.lineno}, col {err.col}\n".encode())


class Server(TCPServer):
    nodeid: ID
    db: DB
    clients: Dict[ID, Conn]

    def __init__(self, *args, **kwargs):
        self.db = DB()
        self.nodeid = gen_id()
        self.clients: Dict[str, Conn] = {}

        TCPServer.__init__(self, *args, **kwargs)

    def server_activate(self):
        super().server_activate()
        self.logger.msg("listening")

    def finish_request(self, request, client_address):
        self.logger.msg(
            "client connected", client_address=client_address,
        )

        super().finish_request(request, client_address)

        self.logger.msg(
            "client disconnected", client_address=client_address,
        )

    @property
    def logger(self):
        return _LOGGER.bind(
            nodeid=id_to_str(self.nodeid), server_address=self.server_address
        )


def _main():
    parser = ArgumentParser(description="jdb server")
    parser.add_argument("-p", "--port", help="port", default=1337, type=int)
    parser.add_argument("-o", "--host", help="host", default="127.0.0.1", type=str)
    args = parser.parse_args()

    with Server((args.host, args.port), Conn) as server:
        server.serve_forever()


if __name__ == "__main__":
    _main()
