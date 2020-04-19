from typing import Tuple, Optional
from collections import OrderedDict
from socketserver import ThreadingTCPServer, StreamRequestHandler
from argparse import ArgumentParser
from pyparsing import ParseException
from structlog import get_logger
from jdb.jql import JQL
from jdb.const import SYNTAX_ERR, TERMINATOR
from jdb.db import DB
from jdb.util import id_to_str, gen_id
from jdb.types import ID

_LOGGER = get_logger()


class Conn(StreamRequestHandler):
    """client connection"""

    client_id: ID
    jql: JQL

    def setup(self):
        """override"""

        super().setup()

        self.client_id = gen_id()
        self.server.clients[self.client_id] = self
        self.jql = JQL(db=self.server.db)
        self.logger = self.server.logger.bind(
            client_id=id_to_str(self.client_id), client_address=self.client_address
        )
        self.server.client_connected(self)

    def finish(self):
        super().finish()

        self.server.client_disconnected(self)

    def handle(self):
        """override"""

        super().handle()

        statement = ""

        for data in self.rfile:
            raw = data.decode().rstrip()

            if not raw:
                break

            statement += f"{raw}\n"
            stripped = statement.rstrip()

            if stripped[-1:] == TERMINATOR:
                self._call(statement)
                statement = ""

    def _call(self, statement: str):
        """send statement to parser for execution"""

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


class Server(ThreadingTCPServer):
    """db server"""

    nodeid: ID
    db: DB
    clients: OrderedDict

    def __init__(self, addr: Tuple[str, int], max_connections: Optional[int] = 100):
        self.db = DB()
        self.nodeid = gen_id()
        self.max_connections = max_connections
        self.clients = OrderedDict()

        ThreadingTCPServer.__init__(self, addr, Conn)

    def client_connected(self, client: Conn):
        self.clients[client.client_id] = client

        self.logger.msg(
            "client connected", client_address=client.client_address,
        )

    def client_disconnected(self, client: Conn):
        del self.clients[client.client_id]

        self.logger.msg(
            "client disconnected", client_address=client.client_address,
        )

    def server_activate(self):
        super().server_activate()

        self.logger.msg("listening")

    @property
    def logger(self):
        """bound logger"""

        return _LOGGER.bind(
            nodeid=id_to_str(self.nodeid), server_address=self.server_address
        )


def _main():
    parser = ArgumentParser(description="jdb server")
    parser.add_argument("-p", "--port", help="port", default=1337, type=int)
    parser.add_argument("-o", "--host", help="host", default="127.0.0.1", type=str)
    parser.add_argument(
        "-c", "--max-connections", help="max connections", default=100, type=int
    )
    args = parser.parse_args()
    addr = (args.host, args.port)

    with Server(addr, max_connections=args.max_connections) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    _main()
