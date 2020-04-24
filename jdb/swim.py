from typing import Any
from threading import Thread
from random import choice, uniform
from time import sleep
from structlog import get_logger
from jdb import node as nde, util

_LOGGER = get_logger()
_JITTER = 0.05


class FailureDetector:
    """detect failures"""

    def __init__(
        self, interval: float, subgroup_size: int, logger: Any, node: nde.Node
    ):
        self.interval = interval
        self.subgroup_size = subgroup_size
        self.logger = logger
        self.node = node

    def loop(self):
        """main loop"""

        while True:
            self.probe()
            sleep(uniform(self.interval - _JITTER, self.interval + _JITTER))

    def probe(self):
        """implement probing"""

        peers = self.node.peers

        if not peers:
            return

        peer = choice(list(peers.values()))

        while peer.node_id == self.node.node_id:
            peer = choice(list(peers.values()))

        peer_id = util.id_to_str(peer.node_id)

        try:
            peer.membership_ping()
            self.logger.info("swim.failure_detector.pass", peer_id=peer_id)
        except Exception:
            self.logger.info("swim.failure_detector.fail", peer_id=peer_id)


class Dissemination:
    """gossip with other nodes"""

    def __init__(self, interval: float, logger: Any):
        self.interval = interval
        self.logger = logger

    def loop(self):
        """main loop"""

        while True:
            sleep(uniform(self.interval - _JITTER, self.interval + _JITTER))


class SWIM:
    """implementation of SWIM protocol"""

    def __init__(
        self,
        node: nde.Node,
        failure_detection_interval: float = 1,
        failure_detection_subgroup_size: int = 3,
        gossip_interval: float = 0.2,
    ):
        node_id = util.id_to_str(node.node_id) if node.node_id else None
        self.logger = _LOGGER.bind(node_id=node_id)
        self.failure_detector = FailureDetector(
            interval=failure_detection_interval,
            subgroup_size=failure_detection_subgroup_size,
            logger=self.logger,
            node=node,
        )

        self.dissemination = Dissemination(interval=gossip_interval, logger=self.logger)
        self.node = node

    def start(self):
        """fire up both components"""

        threads = [
            Thread(target=self.failure_detector.loop, daemon=True),
            Thread(target=self.dissemination.loop, daemon=True),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
