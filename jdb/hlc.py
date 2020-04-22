from __future__ import annotations
from threading import Lock
from dataclasses import dataclass
from jdb import util, types


@dataclass
class HLCTimestamp:
    """hybrid logical clock timestamp"""

    ts: int
    count: int
    node_id: types.ID

    @classmethod
    def from_int(cls, packed: int) -> HLCTimestamp:
        """unpack"""

        string = str(packed)
        node_id = int(string[-14:])
        count = int(string[-16:-14])
        ts = int(string[:-16] or "0")

        return cls(ts=ts, count=count, node_id=node_id)

    def compare(self, other: HLCTimestamp) -> int:
        """compare ts"""

        if self.ts == other.ts:
            if self.count == other.count:
                if self.node_id == other.node_id:
                    return 0
                return self.node_id - other.node_id
            return self.count - other.count
        return self.ts - other.ts

    def __int__(self):
        """pack. v naive implementation. redo for real sometime"""

        string = "".join(
            [str(self.ts), str(self.count).zfill(2), str(self.node_id).zfill(14)]
        )

        return int(string)


class HLC:
    """hybrid logical clock"""

    def __init__(self, node_id: types.ID):
        self.ts = util.now_ms()
        self.count = 0
        self.lock = Lock()
        self.node_id = node_id

    def incr(self) -> HLCTimestamp:
        """get new ts"""

        with self.lock:
            now = util.now_ms()

            if now > self.ts:
                self.ts = now
            else:
                self.count += 1

            return HLCTimestamp(ts=self.ts, count=self.count, node_id=self.node_id)
