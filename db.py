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

            CREATE TABLE IF NOT EXISTS disciplines_metres(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL, -- prebuilt display label "100m Freestyle (25m)"
                stroke TEXT NOT NULL,   -- used for filtering and querying
                distance INTEGER NOT NULL,
                pool_id INTEGER NOT NULL,
                is_relay INTEGER NOT NULL DEFAULT 0,
                CONSTRAINT fk_disciplines_metres_pools
                    FOREIGN KEY(pool_id)
                    REFERENCES pools(id)
            );

            CREATE TABLE IF NOT EXISTS disciplines_yards(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL, -- prebuilt display label "100y Freestyle"
                stroke TEXT NOT NULL,   -- used for filtering and querying
                distance INTEGER NOT NULL,
                is_relay INTEGER NOT NULL DEFAULT 0
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

            CREATE TABLE IF NOT EXISTS performances_metres(
                id INTEGER PRIMARY KEY,
                swimmer_id INTEGER NOT NULL,
                meet_id INTEGER NOT NULL,
                discipline_metres_id INTEGER NOT NULL,
                time_cs INTEGER NOT NULL,    -- stored in centiseconds
                date TEXT NOT NULL, -- stored as YYYY-MM-DD
                session TEXT,   -- AM or PM, optional
                notes TEXT,  -- optional
                CONSTRAINT fk_performances_metres_swimmers
                    FOREIGN KEY(swimmer_id)
                    REFERENCES swimmers(id),
                CONSTRAINT fk_performances_metres_meets
                    FOREIGN KEY(meet_id)
                    REFERENCES meets(id),
                CONSTRAINT fk_performances_metres_disciplines_metres
                    FOREIGN KEY(discipline_metres_id)
                    REFERENCES disciplines_metres(id)
             );

             CREATE TABLE IF NOT EXISTS performances_yards(
                id INTEGER PRIMARY KEY,
                swimmer_id INTEGER NOT NULL,
                meet_id INTEGER NOT NULL,
                discipline_yards_id INTEGER NOT NULL,
                time_cs INTEGER NOT NULL,    -- stored in centiseconds
                date TEXT NOT NULL, -- stored as YYYY-MM-DD
                session TEXT,   -- AM or PM, optional
                notes TEXT,  -- optional
                CONSTRAINT fk_performances_yards_swimmers
                    FOREIGN KEY(swimmer_id)
                    REFERENCES swimmers(id),
                CONSTRAINT fk_performances_yards_meets
                    FOREIGN KEY(meet_id)
                    REFERENCES meets(id),
                CONSTRAINT fk_performances_yards_disciplines_yards
                    FOREIGN KEY(discipline_yards_id)
                    REFERENCES disciplines_yards(id)
             );

             CREATE TABLE IF NOT EXISTS relay_legs_metres(
                id INTEGER PRIMARY KEY,
                performance_metres_id INTEGER NOT NULL, -- time of team
                swimmer_id INTEGER NOT NULL,
                leg_number INTEGER NOT NULL,
                stroke TEXT NOT NULL,
                time_cs INTEGER NOT NULL,  -- time of individual swimmer's leg
                start_type TEXT NOT NULL,   -- 'standing' or 'flying'
                is_mixed_mf INTEGER NOT NULL DEFAULT 0,    -- gender M/F
                CONSTRAINT fk_relay_legs_metres_performances_metres
                    FOREIGN KEY(performance_metres_id)
                    REFERENCES performances_metres(id),
                CONSTRAINT fk_relay_legs_metres_swimmer
                    FOREIGN KEY(swimmer_id)
                    REFERENCES swimmers(id)
            );

            CREATE TABLE IF NOT EXISTS relay_legs_yards(
                id INTEGER PRIMARY KEY,
                performance_yards_id INTEGER NOT NULL, -- time of team
                swimmer_id INTEGER NOT NULL,
                leg_number INTEGER NOT NULL,
                stroke TEXT NOT NULL,
                time_cs INTEGER NOT NULL,  -- time of individual swimmer's leg
                start_type TEXT NOT NULL,   -- 'standing' or 'flying'
                is_mixed_mf INTEGER NOT NULL DEFAULT 0,    -- gender M/F
                CONSTRAINT fk_relay_legs_yards_performances_yards
                    FOREIGN KEY(performance_yards_id)
                    REFERENCES performances_yards(id),
                CONSTRAINT fk_relay_legs_yards_swimmer
                    FOREIGN KEY(swimmer_id)
                    REFERENCES swimmers(id)
            );

        """)
        _seed_pools(conn)
        _seed_countries(conn)
        _seed_disciplines_metres(conn)
        _seed_disciplines_yards(conn)

def _seed_pools(conn):
    """
    Seed the pools table with standard competitive pool sizes on first run.
    """
    if conn.execute("SELECT COUNT(*) FROM pools").fetchone()[0] > 0:
        return  # already seeded
    conn.executemany(
        "INSERT INTO pools (length, unit, name) VALUES (?, ?, ?)",
        [
        (25, "metres", "Short Course 25 Metres"),
        (50, "metres", "Long Course 50 Metres"),
        (33, "metres", "Mid Course 33 Metres"),
        (25, "yards", "Short Course 25 Yards"),
        ]
    )

def _seed_countries(conn):
    """
    Seed the countries table with the ISO alpha-3 list.
    """
    if conn.execute("SELECT COUNT(*) FROM countries").fetchone()[0] > 0:
        return  # already seeded
    conn.executemany(
        "INSERT INTO countries (name, code) VALUES (?, ?)",
        [(c.name, c.alpha_3) for c in pycountry.countries]
    )

def _seed_disciplines_metres(conn):
    """
    Seed the disciplines (meters) table with olympic and non-olympic events.
    """
    if conn.execute("SELECT COUNT(*) FROM disciplines_metres").fetchone()[0] > 0:
        return  # already seeded

    # Build a pool name -> id lookup dictionary to avoid repeated SQL queries
    pools = {
            row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM pools")
            }

    individual = [
        ("Freestyle",    [25, 50, 100, 200, 400, 800, 1500]),
        ("Backstroke",   [25, 50, 100, 200]),
        ("Breaststroke", [25, 50, 100, 200]),
        ("Butterfly",    [25, 50, 100, 200]),
        ("Medley",       [100, 200, 400]),
    ]

    disciplines = []
    for stroke, distances in individual:
        for distance in distances:
            # determine which pools apply
            if distance == 25:
                applicable_pools = ["Short Course 25 Metres"]
            elif distance == 50:
                applicable_pools = ["Short Course 25 Metres", "Long Course 50 Metres"]
            elif stroke == "Medley" and distance == 100:
                applicable_pools = ["Short Course 25 Metres"]
            else:
                applicable_pools = ["Short Course 25 Metres", "Long Course 50 Metres",
                                    "Mid Course 33 Metres"
                                   ]

            for pool_name in applicable_pools:
                pool_id = pools[pool_name]
                name = f"{distance}m {stroke} ({pool_name})"
                disciplines.append((name, stroke, distance, pool_id, 0))

    # Relay events are hard-coded rather than generated programmatically
    relays = [
        ("4x25m Freestyle Relay",  "Freestyle", 100, pools["Short Course 25 Metres"], 1),
        ("4x50m Freestyle Relay",  "Freestyle", 200, pools["Short Course 25 Metres"], 1),
        ("4x100m Freestyle Relay", "Freestyle", 400, pools["Short Course 25 Metres"], 1),
        ("4x200m Freestyle Relay", "Freestyle", 800, pools["Short Course 25 Metres"], 1),
        ("4x50m Medley Relay",     "Medley",    200, pools["Short Course 25 Metres"], 1),
        ("4x100m Medley Relay",    "Medley",    400, pools["Short Course 25 Metres"], 1),
        ("4x50m Freestyle Relay",  "Freestyle", 200, pools["Long Course 50 Metres"], 1),
        ("4x100m Freestyle Relay", "Freestyle", 400, pools["Long Course 50 Metres"], 1),
        ("4x200m Freestyle Relay", "Freestyle", 800, pools["Long Course 50 Metres"], 1),
        ("4x50m Medley Relay",     "Medley",    200, pools["Long Course 50 Metres"], 1),
        ("4x100m Medley Relay",    "Medley",    400, pools["Long Course 50 Metres"], 1),
        ("4x100m Freestyle Relay", "Freestyle", 400, pools["Mid Course 33 Metres"], 1),
        ("4x200m Freestyle Relay", "Freestyle", 800, pools["Mid Course 33 Metres"], 1),
        ("4x100m Medley Relay",    "Medley",    400, pools["Mid Course 33 Metres"], 1),
    ]

    disciplines.extend(relays)

    conn.executemany(
        """INSERT INTO disciplines_metres (name, stroke, distance, pool_id, is_relay)
        VALUES (?, ?, ?, ?, ?)""", disciplines
    )

def _seed_disciplines_yards(conn):
    """
    Seed the disciplines (yards) table.
    """
    if conn.execute("SELECT COUNT(*) FROM disciplines_yards").fetchone()[0] > 0:
        return  # already seeded

    individual = [
        ("Freestyle",    [25, 50, 100, 200, 500, 1000, 1650]),
        ("Backstroke",   [25, 50, 100, 200]),
        ("Breaststroke", [25, 50, 100, 200]),
        ("Butterfly",    [25, 50, 100, 200]),
        ("Medley",       [100, 200, 400]),
    ]

    disciplines = []
    for stroke, distances in individual:
        for distance in distances:
            name = f"{distance}y {stroke}"
            disciplines.append((name, stroke, distance, 0))

    # Relay events are hard-coded rather than generated programmatically
    relays = [
        ("4x25y Freestyle Relay",  "Freestyle", 100, 1),
        ("4x50y Freestyle Relay",  "Freestyle", 200, 1),
        ("4x100y Freestyle Relay", "Freestyle", 400, 1),
        ("4x200y Freestyle Relay", "Freestyle", 800, 1),
        ("4x25y Medley Relay",     "Medley",    100, 1),
        ("4x50y Medley Relay",     "Medley",    200, 1),
        ("4x100y Medley Relay",    "Medley",    400, 1),
    ]

    disciplines.extend(relays)

    conn.executemany(
        """INSERT INTO disciplines_yards (name, stroke, distance, is_relay)
        VALUES (?, ?, ?, ?)""", disciplines
    )
