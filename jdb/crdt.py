from __future__ import annotations
from threading import Lock
from collections import OrderedDict
from itertools import chain
from jdb import types, hlc


class LWWRegister:
    """
    lww register. 2 ops are add/remove. each op adds a ts to its respective set.
    if an element is in remove and has a ts > its counterpart in add, the element has
    been "deleted" from the register
    """

    def __init__(self, replica_id: types.ID):
        self.replica_id = replica_id
        self.clock = hlc.HLC(node_id=replica_id)
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

    def merge(self, other: LWWRegister) -> LWWRegister:
        """merge registers"""

        sets = ["add_set", "remove_set"]
        reg = LWWRegister(replica_id=self.replica_id)

        for a_set in sets:
            my_set, other_set = (
                getattr(self, a_set).items(),
                getattr(other, a_set).items(),
            )

            for elem, ts in chain(my_set, other_set):
                existing = getattr(reg, a_set).get(elem)

                if not existing:
                    getattr(reg, a_set)[elem] = ts
                    continue

                ts_hlc = hlc.HLCTimestamp.from_int(ts)
                ex_hlc = hlc.HLCTimestamp.from_int(existing)

                if ts_hlc.compare(ex_hlc) > 0:
                    getattr(reg, a_set)[elem] = ts

        return reg
