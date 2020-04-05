from pytest import fixture
from jdb.avltree import AVLTree


@fixture
def tree():
    def comparator(i: int, j: int):
        if i == j:
            return 0
        elif i < j:
            return -1

        return 1

    return AVLTree[int](comparator=comparator)


def test_basic(tree: AVLTree):
    tree.insert(1)
    tree.insert(2)
    tree.insert(3)
    tree.insert(4)
    tree.insert(5)
    tree.insert(6)

    assert tree.search(3) == 3
    assert not tree.search(7)
