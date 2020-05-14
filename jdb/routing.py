from typing import Union, List, Optional
import re
from dataclasses import dataclass, field
from structlog import get_logger
from jdb.types import Key, Value
from jdb.errors import InvalidRequest
from jdb import membership as mbr

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
    def key(self) -> Key:
        """key that is used to route the request"""

        result: Optional[bytes] = None

        for req in self.requests:
            match = KEY_REGEX.match(req.key.decode())

            if not match:
                raise InvalidRequest("key must be in /table/key format")

            table, _ = match.groups()

            if not result:
                result = table.encode()
            elif table.encode() != result:
                raise InvalidRequest("cross-table transactions not supported")

        if not result:
            raise InvalidRequest("unable to determine key for request")

        return result


class Router:
    """handle request routing"""

    def __init__(self, membership: mbr.Membership):
        self.membership = membership

    def request(self, _req: BatchRequest) -> bool:
        """send a request"""

        return True
