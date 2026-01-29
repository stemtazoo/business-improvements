from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def connect(db_path: str) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(db_path)
    try:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
