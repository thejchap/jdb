import matplotlib.pyplot as plt

MEMORY = {
    "jdb": [51.841734918, 39.98755088],
    "redis": [12.029713754, 10.795880972],
}


def _main():
    """plot results"""

    width = 0.2

    for i, (store, vals) in enumerate(MEMORY.items()):
        plt.bar(
            [j + i * width for j in range(0, len(vals))], vals, width=width, label=store
        )

    plt.title("in-memory data loading performance")
    plt.legend(loc="best")
    plt.xticks([0, 1], ("v1", "v2"))
    plt.xlabel("store")
    plt.ylabel("seconds")
    plt.show()


if __name__ == "__main__":
    _main()
