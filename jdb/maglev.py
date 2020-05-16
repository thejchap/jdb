from typing import Set, List
from sympy import nextprime
from xxhash import xxh32_intdigest
import jdb.const as const


class Maglev:
    """implement Maglev hashing"""

    def __init__(self, nodes: Set[str]):
        self.nodes = list(nodes)
        self.n = len(nodes)
        self.m = nextprime(self.n * 100)
        self._permutation = self._gen_permutation()
        self.table = self._populate()

    def _gen_permutation(self) -> List[List[int]]:
        """generate permutations"""

        m = self.m
        permutation: List[List[int]] = []

        for i, name in enumerate(list(self.nodes)):
            offset = xxh32_intdigest(name, seed=const.MAGLEV_OFFSET_SEED) % m
            skip = xxh32_intdigest(name, seed=const.MAGLEV_SKIP_SEED) % (m - 1) + 1
            permutation.append([])

            for j in range(0, m):
                permutation[i].append((offset + j * skip) % m)

        return permutation

    def lookup(self, key: str) -> str:
        """lookup node for key"""

        hashed = xxh32_intdigest(key)
        return self.nodes[self.table[hashed % self.m]]

    def _populate(self):
        """generate lookup table"""

        if not self.nodes:
            return

        n, m, perm = self.n, self.m, self._permutation
        next_ = [0] * n
        entry = [-1] * m
        k = 0

        while True:
            for i in range(0, n):
                c = perm[i][next_[i]]

                while entry[c] >= 0:
                    next_[i] += 1
                    c = perm[i][next_[i]]

                entry[c] = i
                next_[i] += 1
                k += 1

                if k == m:
                    return entry
