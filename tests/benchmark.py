from jdb.db import DB
from jdb.errors import TableOverflow

db = DB()
key = b"\0" * 20
val = b"\0" * 100


def put():
    db.put(key, val)


def fill() -> bool:
    while True:
        try:
            db.put(key, val)
        except TableOverflow:
            break

    return True


def delete():
    db.delete(key)


if __name__ == "__main__":
    fill()
