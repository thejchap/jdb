from threading import Thread
from functools import cached_property
from dataclasses import dataclass, field
from argparse import ArgumentParser
from structlog import get_logger
from jdb.util import id_to_str
from jdb import server, node

_LOGGER = get_logger()


@dataclass
class Server:
    """top-level server. starts client and peer servers in threads"""

    host: str
    peer_server_host: str
    port: int
    peer_server_port: int
    max_connections: int
    _client_server: server.ClientServer = field(init=False)
    _peer_server: server.PeerServer = field(init=False)
    _node: node.Node = node.Node()

    def __post_init__(self):
        self._client_server = server.ClientServer(
            addr=(self.host, self.port),
            database=self._node.database,
            max_connections=self.max_connections,
            logger=self.logger,
        )

        self._peer_server = server.PeerServer(
            addr=(self.peer_server_host, self.peer_server_port),
            database=self._node.database,
            logger=self.logger,
        )

    def start(self):
        threads = [
            Thread(target=self._start_client_server, daemon=True),
            Thread(target=self._start_peer_server, daemon=True),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def _start_peer_server(self):
        with self._peer_server as pserver:
            pserver.serve_forever()

    def _start_client_server(self):
        with self._client_server as cserver:
            cserver.serve_forever()

    @cached_property
    def logger(self):
        """bound logger"""

        return _LOGGER.bind(node_id=id_to_str(self._node.node_id))


def _main():
    """main entry point"""

    parser = ArgumentParser(description="jdb server")

    parser.add_argument("-p", "--port", help="port", default=1337, type=int)
    parser.add_argument("-o", "--host", help="host", default="127.0.0.1", type=str)
    parser.add_argument("-r", "--peer-server-port", help="port", default=1338, type=int)
    parser.add_argument(
        "-s", "--peer-server-host", help="host", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "-c", "--max-connections", help="max connections", default=100, type=int
    )
    args = parser.parse_args()

    srv = Server(
        host=args.host,
        port=args.port,
        max_connections=args.max_connections,
        peer_server_host=args.peer_server_host,
        peer_server_port=args.peer_server_port,
    )

    srv.start()


if __name__ == "__main__":
    _main()
