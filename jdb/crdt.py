from threading import Lock
from collections import OrderedDict
from jdb import types, hlc


class LWWRegister:
    def __init__(self, replica_id: types.ID):
        self.replica_id = replica_id
        self.clock = hlc.HLC()
        self.add_set: OrderedDict = OrderedDict()
        self.remove_set: OrderedDict = OrderedDict()
        self.lock = Lock()

    def __iter__(self):
        for elem, ts in self.add_set.items():
            if elem in self.remove_set and self.remove_set[elem] > ts:
                continue
            yield elem, ts

    def add(self, element: bytes):
        with self.lock:
            self.add_set[element] = int(self.clock.incr())

    def remove(self, element: bytes):
        with self.lock:
            self.remove_set[element] = int(self.clock.incr())
