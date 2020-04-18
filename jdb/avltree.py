from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Optional
from jdb import types


@dataclass
class Node(Generic[types.T]):
    key: types.T
    comparator: types.Comparator
    left: Optional[Node[types.T]] = None
    right: Optional[Node[types.T]] = None
    height: int = 0
    balance_factor: int = 0

    def search(self, key: types.T) -> Optional[types.T]:
        cmp = self.comparator(key, self.key)

        if cmp < 0:
            return self.left.search(key) if self.left else None
        elif cmp > 0:
            return self.right.search(key) if self.right else None

        return self.key

    def insert(self, node: Node[types.T]) -> None:
        cmp = self.comparator(node.key, self.key)

        if cmp == 0:
            self.key = node.key
        elif cmp < 0:
            if self.left:
                self.left.insert(node)
            else:
                self.left = node
        elif cmp > 0:
            if self.right:
                self.right.insert(node)
            else:
                self.right = node

        lh = self.left.height if self.left else 0
        rh = self.right.height if self.right else 0

        self.height = 1 + max(lh, rh)
        self.balance_factor = lh - rh

        if self.balance_factor == 2:
            pass
        elif self.balance_factor == -2:
            pass


class AVLTree(Generic[types.T]):
    root: Optional[Node[types.T]] = None

    def __init__(self, comparator: types.Comparator):
        self._cmp = comparator

    def search(self, key: types.T) -> Optional[types.T]:
        return self.root.search(key) if self.root else None

    def insert(self, key: types.T) -> None:
        node = Node[types.T](key=key, comparator=self._cmp)

        if self.root:
            self.root.insert(node)
        else:
            self.root = node
