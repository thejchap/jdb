from typing import Any, Tuple, Optional
from threading import Thread
from collections import OrderedDict
from uuid import uuid4 as uuid
from socketserver import StreamRequestHandler, ThreadingTCPServer
from structlog import get_logger
from pyparsing import ParseException
from jdb import jql, const, node as nde

_LOGGER = get_logger()


class Client(StreamRequestHandler):
    """client connection"""

    logger: Any

    def setup(self):
        """override"""

        super().setup()

        addr = self.client_address

        self.client_id = str(uuid())
        self.jql = jql.JQL(node=self.server.node)
        self.logger = self.server.logger.bind(
            client_id=self.client_id, client_addr=f"{addr[0]}:{addr[1]}",
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
            result, response = self.jql.call(statement=statement)

            self.logger.debug("result", result=result, response=response)

            if result:
                self.wfile.write(f"{result}\n".encode())
            elif response:
                txn = response.txn

                if txn.returning:
                    for _, v in txn.returning.items():
                        self.wfile.write(f"{v.decode() if v else ''}\n".encode())
                else:
                    self.wfile.write(f"{txn.txnid} {const.COMMITTED}\n".encode())
            elif txn.isaborted:
                self.wfile.write(f"{txn.txnid} {const.ABORTED}\n".encode())
            elif txn.ispending:
                self.wfile.write(f"{txn.txnid} {const.PENDING}\n".encode())
        except ParseException as err:
            self.logger.err(err)

            self.wfile.write(
                f"{const.SYNTAX_ERR}: ln {err.lineno}, col {err.col}\n".encode()
            )


class ClientServer(ThreadingTCPServer):
    """server for client communication"""

    allow_reuse_address = True
    daemon_threads = True
    clients: OrderedDict

    def __init__(
        self,
        addr: Tuple[str, int],
        node: nde.Node,
        max_connections: Optional[int] = 100,
    ):
        self.max_connections = max_connections
        self.clients = OrderedDict()
        self.node = node
        self.logger = _LOGGER.bind(addr=f"{addr[0]}:{addr[1]}")

        super().__init__(addr, Client)

    def process_request(self, request, client_address):
        """override"""

        thread = Thread(
            target=self.process_request_thread,
            args=(request, client_address),
            daemon=self.daemon_threads,
            name=f"ClientRequestThread-{':'.join(map(str, client_address))}",
        )

        if not thread.daemon and self.block_on_close:
            if self._threads is None:
                self._threads = []
            self._threads.append(thread)

        thread.start()

    def client_connected(self, client: Client):
        """add client"""

        self.clients[client.client_id] = client
        addr = client.client_address
        self.logger.msg("client.connected", client_address=f"{addr[0]}:{addr[1]}")

    def client_disconnected(self, client: Client):
        """remove client"""

        del self.clients[client.client_id]
        addr = client.client_address
        self.logger.msg("client.disconnected", client_address=f"{addr[0]}:{addr[1]}")

    def server_activate(self):
        """override"""

        super().server_activate()
        self.logger.msg("client_server.listening")

    def shutdown(self):
        "shut it down"

        super().shutdown()
        self.logger.msg("client_server.shutdown")
