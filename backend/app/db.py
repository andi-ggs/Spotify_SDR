import sqlite3
from contextlib import contextmanager
from .config import SQLITE_PATH


@contextmanager
def get_db():
    con = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    try:
        yield con
    finally:
        con.close()
