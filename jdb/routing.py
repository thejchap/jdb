from typing import Union, List, Optional, Dict
import re
from dataclasses import dataclass, field
from structlog import get_logger
from jdb.types import Key, Value
from jdb.errors import InvalidRequest
import jdb.membership as mbr
import jdb.node as nde
import jdb.types as types

LOGGER = get_logger()
KEY_REGEX = re.compile(r"^\/([A-Za-z0-9]+)\/([A-Za-z0-9]+)$")


@dataclass
class DeleteRequest:
    key: Key


@dataclass
class PutRequest:
    key: Key
    value: Value


@dataclass
class GetRequest:
    key: Key


RequestUnion = Union[PutRequest, GetRequest, DeleteRequest]


@dataclass
class BatchRequest:
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

    def __init__(self, membership: mbr.Membership, node: "nde.Node"):
        self._membership = membership
        self._node = node

    def request(self, req: BatchRequest) -> Dict[types.Key, types.Value]:
        """send a request"""

        peer = self._membership.lookup_leaseholder(req.key)

        if not peer:
            coord_name = self._node.name
            return self._node.coordinate(req)

        coord_name = peer.name

        LOGGER.info("routing.request.coordinator_found", coordinator=coord_name)
        return {}
