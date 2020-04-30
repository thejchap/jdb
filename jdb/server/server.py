from threading import Thread
from typing import Optional
from dataclasses import dataclass, field
from argparse import ArgumentParser
from jdb import server, node, util


@dataclass
class Server:
    """top-level server. starts client and peer servers in threads"""

    port: Optional[int] = 1337
    p2p_port: Optional[int] = 1338
    max_connections: Optional[int] = 100
    host: Optional[str] = "127.0.0.1"
    p2p_host: Optional[str] = "127.0.0.1"
    join: Optional[str] = None
    node_id: Optional[str] = None
    _client_server: server.ClientServer = field(init=False)
    _peer_server: server.PeerServer = field(init=False)
    _node: node.Node = field(init=False)
    p2p_addr: str = field(init=False)

    def __post_init__(self):
        """override"""

        p2p_addr = f"{self.p2p_host}:{self.p2p_port}"
        self.p2p_addr = p2p_addr
        client_addr = f"{self.host}:{self.port}"
        node_id = util.id_from_str(self.node_id) if self.node_id else util.gen_id()
        self.node_id = node_id

        self._node = node.Node(
            p2p_addr=p2p_addr, client_addr=client_addr, node_id=node_id,
        )

        if self.join:
            self._node.bootstrap(self.join)

        self._client_server = server.ClientServer(
            addr=(self.host, self.port),
            node=self._node,
            max_connections=self.max_connections,
        )

        self._peer_server = server.PeerServer(
            addr=(self.p2p_host, self.p2p_port), node=self._node
        )

    def start(self):
        """fire up server for client comms and p2p comms"""

        threads = [
            Thread(
                target=self._start_client_server, daemon=True, name="ClientServerThread"
            ),
            Thread(
                target=self._start_peer_server, daemon=True, name="PeerServerThread"
            ),
            Thread(target=self._start_membership, daemon=True, name="MembershipThread"),
        ]

        for thread in threads:
            thread.start()

        try:
            for thread in threads:
                thread.join()
        except (KeyboardInterrupt, SystemExit):
            self.stop()

    def stop(self):
        """shut it down"""

        self._client_server.shutdown()
        self._peer_server.shutdown()
        self._node.membership.stop()

    def _start_peer_server(self):
        """start up peer grpc server"""

        self._peer_server.serve_forever()

    def _start_membership(self):
        """start up peer grpc server"""

        self._node.membership.start()

    def _start_client_server(self):
        """start up server for client requests"""

        with self._client_server as cserver:
            cserver.serve_forever()


def _main():
    """main entry point"""

    parser = ArgumentParser(description="jdb server")

    parser.add_argument(
        "-p", "--port", help="port for client connections", default=1337, type=int
    )
    parser.add_argument(
        "-o",
        "--host",
        help="host for client connections",
        default="127.0.0.1",
        type=str,
    )
    parser.add_argument("-i", "--node-id", help="node id", type=str)
    parser.add_argument("-j", "--join", help="node address to join", type=str)
    parser.add_argument(
        "-r", "--p2p-port", help="port for p2p communication", default=1338, type=int,
    )
    parser.add_argument(
        "-s",
        "--p2p-host",
        help="host for p2p communication",
        default="127.0.0.1",
        type=str,
    )
    parser.add_argument(
        "-c", "--max-connections", help="max connections", default=100, type=int
    )
    args = parser.parse_args()

    srv = Server(
        host=args.host,
        port=int(args.port),
        join=args.join,
        max_connections=args.max_connections,
        p2p_host=args.p2p_host,
        p2p_port=int(args.p2p_port),
        node_id=args.node_id,
    )

    srv.start()


if __name__ == "__main__":
    _main()
