import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".swimsql" / "swimsql.db"

def get_connection():
    """
    Open and return a configured connection to the SQLite database.
    Creates the directory if it does not exist.
    Rows are accessible by column name via sqlite3.Row.
    Foreign key constraints are enforced.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # access rows by column name (Python-level)
    conn.row_factory = sqlite3.Row

    # PRAGMA sets SQLite configuration (SQLite-level)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
