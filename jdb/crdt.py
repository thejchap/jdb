from __future__ import annotations
from threading import Lock
from collections import OrderedDict
from jdb import types, hlc


class LWWRegister:
    """
    lww register. 2 ops are add/remove. each op adds a ts to its respective set.
    if an element is in remove and has a ts > its counterpart in add, the element has
    been "deleted" from the register
    """

    def __init__(self, replica_id: types.ID):
        self.replica_id = replica_id
        self.clock = hlc.HLC()
        self.add_set: OrderedDict = OrderedDict()
        self.remove_set: OrderedDict = OrderedDict()
        self.lock = Lock()

    def __iter__(self):
        """actual representation of state"""

        for elem, ts in self.add_set.items():
            if elem in self.remove_set and self.remove_set[elem] > ts:
                continue
            yield elem, ts

    def add(self, element: bytes):
        """add element to add set"""

        with self.lock:
            self.add_set[element] = int(self.clock.incr())

    def remove(self, element: bytes):
        """add element to remove set"""

        with self.lock:
            self.remove_set[element] = int(self.clock.incr())

    def merge(self, incoming: LWWRegister) -> LWWRegister:
        """threadsafe wrapper"""

        with self.lock:
            return self._merge(incoming)

    def _merge(self, incoming: LWWRegister) -> LWWRegister:
        """merge registers"""

        sets = ["add_set", "remove_set"]

        for key in sets:
            incoming_set = getattr(incoming, key).items()

            for elem, ts in incoming_set:
                ts = int(ts)
                existing = getattr(self, key).get(elem)

                if not existing:
                    getattr(self, key)[elem] = ts
                    continue

                incoming_ts = hlc.HLCTimestamp.from_int(ts)
                my_ts = hlc.HLCTimestamp.from_int(existing)

                self.clock.recv(incoming_ts)

                if incoming_ts.compare(my_ts) > 0:
                    getattr(self, key)[elem] = ts

        return self
