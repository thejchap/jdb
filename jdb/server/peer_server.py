from typing import Tuple, Any
from socketserver import ThreadingTCPServer, StreamRequestHandler
from jdb import db


class Peer(StreamRequestHandler):
    """represents peer client connection"""


class PeerServer(ThreadingTCPServer):
    """server for p2p communication"""

    database: db.DB

    def __init__(self, addr: Tuple[str, int], database: db.DB, logger: Any):
        self.database = database
        self.logger = logger

        super().__init__(addr, Peer)

    def server_activate(self):
        super().server_activate()

        self._logger.msg("peer_server.listening")

    @property
    def _logger(self):
        """bound logger"""

        return self.logger.bind(port=self.server_address[1])
