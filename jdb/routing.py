from typing import Union, List, Optional, Dict
import re
from dataclasses import dataclass, field
from structlog import get_logger
from jdb.types import Key, Value
from jdb.errors import InvalidRequest
import jdb.membership as mbr  # pylint: disable=unused-import
import jdb.node as nde  # pylint: disable=unused-import
import jdb.types as types

LOGGER = get_logger()
KEY_REGEX = re.compile(r"^\/([A-Za-z0-9]+)\/([A-Za-z0-9]+)$")


@dataclass
class DeleteRequest:
    """request type"""

    key: Key


@dataclass
class PutRequest:
    """request type"""

    key: Key
    value: Value


@dataclass
class GetRequest:
    """request type"""

    key: Key


RequestUnion = Union[PutRequest, GetRequest, DeleteRequest]


@dataclass
class BatchRequest:
    """represents a client request to get routed"""

    requests: List[RequestUnion] = field(default_factory=list)

    @property
    def key(self) -> str:
        """key that is used to route the request"""

        result: Optional[str] = None

        for req in self.requests:
            match = KEY_REGEX.match(req.key.decode())

            if not match:
                raise InvalidRequest("key must be in /table/key format")

            table, _ = match.groups()

            if not result:
                result = table
            elif table != result:
                raise InvalidRequest("cross-table transactions not supported")

        if not result:
            raise InvalidRequest("unable to determine key for request")

        return result


class Router:
    """handle request routing"""

    def __init__(self, membership: "mbr.Membership", node: "nde.Node"):
        self._membership = membership
        self._node = node

    def request(self, req: BatchRequest) -> Dict[types.Key, types.Value]:
        """send a request"""

        peer = self._membership.lookup_leaseholder(req.key)

        if not peer:
            LOGGER.info("routing.request.local", key=req.key)
            return self._node.coordinate(req)

        LOGGER.info(
            "routing.request.remote",
            peer_name=peer.name,
            peer_addr=peer.addr,
            table=req.key,
        )

        return peer.coordinate(req)
