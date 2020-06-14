from cProfile import run
from jdb.storage import db

jdb = db.DB(compression=None)

run(
    '[jdb.put(f"key{i}".encode(), b"val") for i in range(0, 1000)]',
    filename="tmp/jdb.prof",
)
