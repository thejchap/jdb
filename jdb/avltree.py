from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Optional, Callable
from jdb import types


@dataclass
class Node(Generic[types.T]):
    """tree nodes"""

    key: types.T
    comparison_key: Callable
    left: Optional[Node[types.T]] = None
    right: Optional[Node[types.T]] = None
    maximum: Optional[Node[types.T]] = None
    height: int = 0
    balance_factor: int = 0

    def __post_init__(self):
        """override"""

        self.maximum = self

    def _compare(self, one: types.T, other: types.T) -> int:
        """simple comparator"""

        keyone, keyother = self.comparison_key(one), self.comparison_key(other)

        if keyone == keyother:
            return 0
        if keyone < keyother:
            return -1

        return 1

    def search(self, key: types.T, gte: Optional[bool] = False) -> Optional[types.T]:
        """
        bst search. if gte is true, find exact match or closest node gte search key
        """

        cmp = self._compare(key, self.key)

        if cmp < 0:
            if gte and (
                not self.left
                or (
                    self._compare(key, self.left.key) > 0
                    and self.left.maximum
                    and self._compare(key, self.left.maximum.key) > 0
                )
            ):
                return self.key

            return self.left.search(key, gte=gte) if self.left else None
        if cmp > 0:
            return self.right.search(key, gte=gte) if self.right else None

        return self.key

    def insert(self, node: Node[types.T]) -> None:
        """bst insert then rebalance if balance factor +/- 2"""

        cmp = self._compare(node.key, self.key)

        if cmp == 0:
            self.key = node.key
        elif cmp < 0:
            if self.left:
                self.left.insert(node)
            else:
                self.left = node
        elif cmp > 0:
            self.maximum = node

            if self.right:
                self.right.insert(node)
            else:
                self.right = node

        lheight = self.left.height if self.left else 0
        rheight = self.right.height if self.right else 0

        self.height = 1 + max(lheight, rheight)
        self.balance_factor = lheight - rheight

        if self.balance_factor == 2:
            pass
        elif self.balance_factor == -2:
            pass


class AVLTree(Generic[types.T]):
    """avl tree implementation"""

    root: Optional[Node[types.T]] = None

    def __init__(self, comparison_key: Callable = lambda x: x):
        self._cmp = comparison_key

    def search(self, key: types.T, gte: Optional[bool] = False) -> Optional[types.T]:
        """proxy to root node"""

        return self.root.search(key, gte=gte) if self.root else None

    def insert(self, key: types.T) -> None:
        """proxy to root node"""

        node = Node[types.T](key=key, comparison_key=self._cmp)

        if self.root:
            self.root.insert(node)
        else:
            self.root = node
