from typing import Any, Tuple, Optional
from collections import OrderedDict
from socketserver import StreamRequestHandler, ThreadingTCPServer
from pyparsing import ParseException
from jdb import types, jql, util, const, db


class Client(StreamRequestHandler):
    """client connection"""

    client_id: types.ID
    jql: jql.JQL
    logger: Any

    def setup(self):
        """override"""

        super().setup()

        addr = self.client_address
        self.client_id = util.gen_id()
        self.server.clients[self.client_id] = self
        self.jql = jql.JQL(db=self.server.database)
        self.logger = self.server.logger.bind(
            client_id=util.id_to_str(self.client_id),
            client_address=f"{addr[0]}:{addr[1]}",
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

            if stripped[-1:] == const.TERMINATOR:
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
            self.wfile.write(
                f"{const.SYNTAX_ERR}: ln {err.lineno}, col {err.col}\n".encode()
            )


class ClientServer(ThreadingTCPServer):
    """server for client communication"""

    clients: OrderedDict
    logger: Any
    database: db.DB

    def __init__(
        self,
        addr: Tuple[str, int],
        database: db.DB,
        logger: Any,
        max_connections: Optional[int] = 100,
    ):
        self.max_connections = max_connections
        self.clients = OrderedDict()
        self.database = database
        self.logger = logger

        super().__init__(addr, Client)

    def client_connected(self, client: Client):
        self.clients[client.client_id] = client
        addr = client.client_address
        self._logger.msg("client.connected", client_address=f"{addr[0]}:{addr[1]}")

    def client_disconnected(self, client: Client):
        del self.clients[client.client_id]
        addr = client.client_address
        self._logger.msg("client.disconnected", client_address=f"{addr[0]}:{addr[1]}")

    def server_activate(self):
        super().server_activate()

        self._logger.msg("client_server.listening")

    @property
    def _logger(self):
        """bound logger"""

        return self.logger.bind(port=self.server_address[1])
