from __future__ import annotations
from threading import Lock
from dataclasses import dataclass
from jdb import util


@dataclass
class HLCTimestamp:
    """hybrid logical clock timestamp"""

    ts: int
    count: int

    @classmethod
    def from_int(cls, packed: int) -> HLCTimestamp:
        """unpack"""

        packed_str = str(packed)
        count = int(packed_str[-4:])
        ts = int(packed_str[0 : len(packed_str) - 4])

        return cls(ts=ts, count=count)

    def __int__(self):
        """pack. v naive implementation. redo for real sometime"""

        return int(f"{str(self.ts).zfill(16)}{str(self.count).zfill(4)}")


class HLC:
    """hybrid logical clock"""

    def __init__(self):
        self.ts = util.now_ms()
        self.count = 0
        self.lock = Lock()

    def incr(self) -> HLCTimestamp:
        """get new ts"""

        with self.lock:
            now = util.now_ms()

            if now > self.ts:
                self.ts = now
            else:
                self.count += 1

            return HLCTimestamp(ts=self.ts, count=self.count)
