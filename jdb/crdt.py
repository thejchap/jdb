from dataclasses import dataclass, field
from collections import OrderedDict
from jdb import types


@dataclass
class LWWRegister:
    replica_id: types.ID
    _ts: int = 0
    _add_set: OrderedDict = field(default_factory=OrderedDict)
    _remove_set: OrderedDict = field(default_factory=OrderedDict)

    def __iter__(self):
        for el, ts in self._add_set:
            if el in self._remove_set and self._remove_set[el] > ts:
                continue
            yield el

    def add(self, element: bytes):
        self._add_set[element] = self._ts
        self._ts += 1

    def remove(self, element: bytes):
        self._remove_set[element] = self._ts
        self._ts += 1
