from jdb.db import Db, LogOverflow

db = Db()
key = b"\0" * 20
val = b"\0" * 100


def put():
    db.put(key, val)


def fill():
    while True:
        try:
            db.put(key, val)
        except LogOverflow:
            break


def delete():
    db.delete(key)
