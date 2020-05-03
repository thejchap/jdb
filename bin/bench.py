from typing import List
from argparse import ArgumentParser
from threading import Thread
from timeit import timeit
from random import getrandbits
from structlog import get_logger
from redis import Redis
from jdb import db

KEY_SIZE = 22
VAL_SIZE = 1024
LOGGER = get_logger()


def _exec_threads(arr: List[Thread]):
    """helper to run a bunch of threads and wait for them to finish"""

    for thread in arr:
        thread.start()

    for thread in arr:
        thread.join()


def main():
    """fire it up"""

    parser = ArgumentParser()
    parser.add_argument(
        "-s",
        "--store",
        type=str,
        help="which store to use",
        choices=["redis", "jdb"],
        required=True,
    )

    parser.add_argument(
        "-z", "--set-size", type=int, help="number of keys to insert", default=1000000
    )

    args = parser.parse_args()
    redis = Redis(host="localhost", port=6379, db=0)
    jdb = db.DB(compression=None)
    builder_threads = []
    writer_threads = []
    thread_count = 32
    n = 1000
    batches = []
    val = bytes(bytearray([1] * VAL_SIZE))

    def redis_txn(batch):
        pipe = redis.pipeline()
        for k, v in batch:
            pipe.set(k, v)
        pipe.execute()

    def jdb_txn(batch):
        with jdb.transaction() as txn:
            for k, v in batch:
                txn.write(k, v)

    funcs = {"redis": redis_txn, "jdb": jdb_txn}
    func = funcs[args.store]

    LOGGER.info(
        "config",
        thread_count=thread_count,
        set_size=args.set_size,
        val_size=VAL_SIZE,
        key_size=KEY_SIZE,
        store=args.store,
    )

    batch_size = int(args.set_size / thread_count)

    def build(i: int):
        for _ in range(0, batch_size):
            key = bytes(getrandbits(8) for _ in range(KEY_SIZE))
            batches[i].append([key, val])

    def populate(i: int):
        batch = batches[i]
        for j in range(0, len(batch), n):
            func(batch[j : j + n])

    for i in range(0, thread_count):
        builder_threads.append(Thread(target=build, args=(i,)))
        writer_threads.append(Thread(target=populate, args=(i,)))
        batches.append([])

    LOGGER.info("setup")
    _exec_threads(builder_threads)
    LOGGER.info("running")
    elapsed = timeit(lambda: _exec_threads(writer_threads), number=1)
    LOGGER.info("done", elapsed=elapsed)


if __name__ == "__main__":
    main()
