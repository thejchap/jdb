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

        string = str(packed)
        count = int(string[-2:])
        ts = int(string[:-2] or "0")

        return cls(ts=ts, count=count)

    def compare(self, other: HLCTimestamp) -> int:
        """compare ts"""

        if self.ts == other.ts:
            if self.count == other.count:
                return 0
            return self.count - other.count
        return self.ts - other.ts

    def __int__(self):
        """pack. v naive implementation. redo for real sometime"""

        return int("".join([str(self.ts).zfill(16), str(self.count).zfill(2)]))


class HLC:
    """hybrid logical clock"""

    def __init__(self):
        self.ts = util.now_ms()
        self.count = 0
        self.lock = Lock()

    def recv(self, incoming: HLCTimestamp):
        """process incoming ts"""

        with self.lock:
            now = util.now_ms()

            if now > self.ts and now > incoming.ts:
                self.ts = now
                self.count = 0
            elif self.ts == incoming.ts:
                self.count = max(self.count, incoming.count)
            elif self.ts > incoming.ts:
                self.count += 1
            else:
                self.ts = incoming.ts
                self.count = incoming.count + 1

    def incr(self) -> HLCTimestamp:
        """get new ts"""

        with self.lock:
            now = util.now_ms()

            if now > self.ts:
                self.ts = now
            else:
                self.count += 1

            return HLCTimestamp(ts=self.ts, count=self.count)
