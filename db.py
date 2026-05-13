import sqlite3
import pycountry
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

def init_db():
    """
    Create all tables if they do not exist.
    Seed reference data on first run.
    """
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pools(
                id INTEGER PRIMARY KEY,
                length INTEGER NOT NULL,
                unit TEXT NOT NULL,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS countries(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS disciplines(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL, -- prebuilt display label "100m Freestyle (25m)"
                stroke TEXT NOT NULL,   -- used for filtering and querying
                distance INTEGER NOT NULL,
                pool_id INTEGER NOT NULL,
                is_relay INTEGER NOT NULL DEFAULT 0,
                CONSTRAINT fk_pools
                    FOREIGN KEY(pool_id)
                    REFERENCES pools(id)
            );

            CREATE TABLE IF NOT EXISTS meets(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                date_start TEXT NOT NULL,   -- stored as YYYY-MM-DD
                date_end TEXT,   -- optional
                location TEXT,   -- optional
                country_id INTEGER NOT NULL,
                notes TEXT,  -- optional
                CONSTRAINT fk_meets_countries
                    FOREIGN KEY(country_id)
                    REFERENCES countries(id)
            );

            CREATE TABLE IF NOT EXISTS clubs(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                country_id INTEGER NOT NULL,
                CONSTRAINT fk_clubs_countries
                    FOREIGN KEY(country_id)
                    REFERENCES countries(id)
            );

            CREATE TABLE IF NOT EXISTS swimmers(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL, -- stored as YYYY-MM-DD
                gender TEXT NOT NULL,    -- M or F
                club_id INTEGER NOT NULL,
                country_id INTEGER NOT NULL,
                CONSTRAINT fk_swimmers_clubs
                    FOREIGN KEY(club_id)
                    REFERENCES clubs(id),
                CONSTRAINT fk_swimmers_countries
                    FOREIGN KEY(country_id)
                    REFERENCES countries(id)
            );

            CREATE TABLE IF NOT EXISTS performances(
                id INTEGER PRIMARY KEY,
                swimmer_id INTEGER NOT NULL,
                meet_id INTEGER NOT NULL,
                discipline_id INTEGER NOT NULL,
                time_cs INTEGER NOT NULL,    -- stored in centiseconds
                date TEXT NOT NULL, -- stored as YYYY-MM-DD
                session TEXT,   -- AM or PM, optional
                notes TEXT,  -- optional
                CONSTRAINT fk_performances_swimmers
                    FOREIGN KEY(swimmer_id)
                    REFERENCES swimmers(id),
                CONSTRAINT fk_performances_meets
                    FOREIGN KEY(meet_id)
                    REFERENCES meets(id),
                CONSTRAINT fk_performances_disciplines
                    FOREIGN KEY(discipline_id)
                    REFERENCES disciplines(id)
             );
        """)
