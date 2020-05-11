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
    height: int = 1

    def __post_init__(self):
        """override"""

        self.maximum = self


class AVLTree(Generic[types.T]):
    """avl tree implementation"""

    root: Optional[Node[types.T]] = None

    def __init__(self, comparison_key: Callable = lambda x: x):
        self._cmp = comparison_key

    def search(self, key: types.T, gte: Optional[bool] = False) -> Optional[types.T]:
        """proxy to root node"""

        return self._search(self.root, key=key, gte=gte)

    def _search(
        self, root: Optional[Node[types.T]], key: types.T, gte: Optional[bool] = False
    ) -> Optional[types.T]:
        """
        bst search. if gte is true, find exact match or closest node gte search key
        """

        if not root:
            return None

        cmp = self._compare(key, root.key)

        if cmp < 0:
            if gte and (
                not root.left
                or (
                    self._compare(key, root.left.key) > 0
                    and root.left.maximum
                    and self._compare(key, root.left.maximum.key) > 0
                )
            ):
                return root.key

            return self._search(root.left, key, gte=gte)
        if cmp > 0:
            return self._search(root.right, key, gte=gte)

        return root.key

    def _compare(self, one: types.T, other: types.T) -> int:
        """simple comparator"""

        keyone, keyother = self._cmp(one), self._cmp(other)

        if keyone == keyother:
            return 0
        if keyone < keyother:
            return -1

        return 1

    def insert(self, key: types.T) -> None:
        """proxy to root node"""

        node = Node[types.T](key=key, comparison_key=self._cmp)
        self.root = self._insert(self.root, node)

    def _insert(
        self, root: Optional[Node[types.T]], node: Node[types.T]
    ) -> Node[types.T]:
        """bst insert then rebalance if balance factor +/- 2"""

        if not root:
            return node

        cmp = self._compare(node.key, root.key)

        if cmp == 0:
            root.key = node.key
        elif cmp < 0:
            root.left = self._insert(root.left, node)
        elif cmp > 0:
            root.maximum = node
            root.right = self._insert(root.right, node)

        lheight = self._getheight(root.left)
        rheight = self._getheight(root.right)
        root.height = 1 + max(lheight, rheight)
        balance = lheight - rheight
        result = root

        if balance > 1 and root.left and self._compare(node.key, root.left.key) < 0:
            result = self._right_rotate(root)
        elif (
            balance < -1 and root.right and self._compare(node.key, root.right.key) > 0
        ):
            result = self._left_rotate(root)
        elif balance > 1 and root.left and self._compare(node.key, root.left.key) > 0:
            root.left = self._left_rotate(root.left)
            result = self._right_rotate(root)
        elif (
            balance < -1 and root.right and self._compare(node.key, root.right.key) < 0
        ):
            root.right = self._right_rotate(root.right)
            result = self._left_rotate(root)

        return result

    def _left_rotate(self, node: Node[types.T]):
        """l rotate"""

        right = node.right
        if not right:
            return node
        rleft = right.left
        right.left = node
        node.right = rleft
        node.height = 1 + max(self._getheight(node.left), self._getheight(node.right))
        right.height = 1 + max(
            self._getheight(right.left), self._getheight(right.right)
        )
        return right

    def _right_rotate(self, node: Node[types.T]):
        """r rotate"""

        left = node.left
        if not left:
            return node
        lright = left.right
        left.right = node
        node.left = lright
        node.height = 1 + max(self._getheight(node.left), self._getheight(node.right))
        left.height = 1 + max(self._getheight(left.left), self._getheight(left.right))
        return left

    def _getheight(self, node: Optional[Node[types.T]]) -> int:
        """helper"""

        if not node:
            return 0

        return node.height
