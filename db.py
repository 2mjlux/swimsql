# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# http://mozilla.org/MPL/2.0/.
# Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)

import sqlite3
import pycountry
from pathlib import Path

DB_PATH = Path.home() / ".swimsql" / "swimsql.db"  # module-level constant


# Setup
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
                is_relay_leg INTEGER NOT NULL DEFAULT 0,  -- 1 if swum during a relay
                leg_number INTEGER,  -- 1-4, NULL if not a relay leg
                is_mixed_mf INTEGER NOT NULL DEFAULT 0,  -- 1 if mixed gender relay
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
                is_relay_leg INTEGER NOT NULL DEFAULT 0,  -- 1 if swum during a relay
                leg_number INTEGER,  -- 1-4, NULL if not a relay leg
                is_mixed_mf INTEGER NOT NULL DEFAULT 0,  -- 1 if mixed gender relay
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

            -- relay_legs_metres and relay_legs_yards are implemented in v2
            -- see README known limitations section
            -- CREATE TABLE IF NOT EXISTS relay_legs_metres(
                -- id INTEGER PRIMARY KEY,
                -- performance_metres_id INTEGER NOT NULL, -- time of team
                -- swimmer_id INTEGER NOT NULL,
                -- leg_number INTEGER NOT NULL,  -- 1=standing start, 2-4=flying start
                -- stroke TEXT NOT NULL,
                -- time_cs INTEGER NOT NULL,  -- time of individual swimmer's leg
                -- is_mixed_mf INTEGER NOT NULL DEFAULT 0,    -- gender M/F
                -- CONSTRAINT fk_relay_legs_metres_performances_metres
                    -- FOREIGN KEY(performance_metres_id)
                    -- REFERENCES performances_metres(id),
                -- CONSTRAINT fk_relay_legs_metres_swimmer
                    -- FOREIGN KEY(swimmer_id)
                    -- REFERENCES swimmers(id)
            -- );

            -- CREATE TABLE IF NOT EXISTS relay_legs_yards(
                -- id INTEGER PRIMARY KEY,
                -- performance_yards_id INTEGER NOT NULL, -- time of team
                -- swimmer_id INTEGER NOT NULL,
                -- leg_number INTEGER NOT NULL,  -- 1=standing start, 2-4=flying start
                -- stroke TEXT NOT NULL,
                -- time_cs INTEGER NOT NULL,  -- time of individual swimmer's leg
                -- is_mixed_mf INTEGER NOT NULL DEFAULT 0,    -- gender M/F
                -- CONSTRAINT fk_relay_legs_yards_performances_yards
                    -- FOREIGN KEY(performance_yards_id)
                    -- REFERENCES performances_yards(id),
                -- CONSTRAINT fk_relay_legs_yards_swimmer
                    -- FOREIGN KEY(swimmer_id)
                    -- REFERENCES swimmers(id)
            -- );

        """)
        _seed_pools(conn)
        _seed_countries(conn)
        _seed_disciplines_metres(conn)
        _seed_disciplines_yards(conn)


# Seeding
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
        ],
    )


def _seed_countries(conn):
    """
    Seed the countries table with the ISO alpha-3 list.
    """
    if conn.execute("SELECT COUNT(*) FROM countries").fetchone()[0] > 0:
        return  # already seeded
    conn.executemany(
        "INSERT INTO countries (name, code) VALUES (?, ?)",
        [(c.name, c.alpha_3) for c in pycountry.countries],
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
        ("Freestyle", [25, 50, 100, 200, 400, 800, 1500]),
        ("Backstroke", [25, 50, 100, 200]),
        ("Breaststroke", [25, 50, 100, 200]),
        ("Butterfly", [25, 50, 100, 200]),
        ("Medley", [100, 200, 400]),
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
                applicable_pools = [
                    "Short Course 25 Metres",
                    "Long Course 50 Metres",
                    "Mid Course 33 Metres",
                ]

            for pool_name in applicable_pools:
                pool_id = pools[pool_name]
                name = f"{distance}m {stroke} ({pool_name})"
                disciplines.append((name, stroke, distance, pool_id, 0))

    # Relay events are hard-coded rather than generated programmatically
    relays = [
        ("4x25m Freestyle Relay", "Freestyle", 100, pools["Short Course 25 Metres"], 1),
        ("4x50m Freestyle Relay", "Freestyle", 200, pools["Short Course 25 Metres"], 1),
        (
            "4x100m Freestyle Relay",
            "Freestyle",
            400,
            pools["Short Course 25 Metres"],
            1,
        ),
        (
            "4x200m Freestyle Relay",
            "Freestyle",
            800,
            pools["Short Course 25 Metres"],
            1,
        ),
        ("4x50m Medley Relay", "Medley", 200, pools["Short Course 25 Metres"], 1),
        ("4x100m Medley Relay", "Medley", 400, pools["Short Course 25 Metres"], 1),
        ("4x50m Freestyle Relay", "Freestyle", 200, pools["Long Course 50 Metres"], 1),
        ("4x100m Freestyle Relay", "Freestyle", 400, pools["Long Course 50 Metres"], 1),
        ("4x200m Freestyle Relay", "Freestyle", 800, pools["Long Course 50 Metres"], 1),
        ("4x50m Medley Relay", "Medley", 200, pools["Long Course 50 Metres"], 1),
        ("4x100m Medley Relay", "Medley", 400, pools["Long Course 50 Metres"], 1),
        ("4x100m Freestyle Relay", "Freestyle", 400, pools["Mid Course 33 Metres"], 1),
        ("4x200m Freestyle Relay", "Freestyle", 800, pools["Mid Course 33 Metres"], 1),
        ("4x100m Medley Relay", "Medley", 400, pools["Mid Course 33 Metres"], 1),
    ]

    disciplines.extend(relays)

    conn.executemany(
        """INSERT INTO disciplines_metres (name, stroke, distance, pool_id, is_relay)
        VALUES (?, ?, ?, ?, ?)""",
        disciplines,
    )


def _seed_disciplines_yards(conn):
    """
    Seed the disciplines (yards) table.
    """
    if conn.execute("SELECT COUNT(*) FROM disciplines_yards").fetchone()[0] > 0:
        return  # already seeded

    individual = [
        ("Freestyle", [25, 50, 100, 200, 500, 1000, 1650]),
        ("Backstroke", [25, 50, 100, 200]),
        ("Breaststroke", [25, 50, 100, 200]),
        ("Butterfly", [25, 50, 100, 200]),
        ("Medley", [100, 200, 400]),
    ]

    disciplines = []
    for stroke, distances in individual:
        for distance in distances:
            name = f"{distance}y {stroke}"
            disciplines.append((name, stroke, distance, 0))

    # Relay events are hard-coded rather than generated programmatically
    relays = [
        ("4x25y Freestyle Relay", "Freestyle", 100, 1),
        ("4x50y Freestyle Relay", "Freestyle", 200, 1),
        ("4x100y Freestyle Relay", "Freestyle", 400, 1),
        ("4x200y Freestyle Relay", "Freestyle", 800, 1),
        ("4x25y Medley Relay", "Medley", 100, 1),
        ("4x50y Medley Relay", "Medley", 200, 1),
        ("4x100y Medley Relay", "Medley", 400, 1),
    ]

    disciplines.extend(relays)

    conn.executemany(
        """INSERT INTO disciplines_yards (name, stroke, distance, is_relay)
        VALUES (?, ?, ?, ?)""",
        disciplines,
    )


# Time helpers
def cs_to_time(cs):
    """
    Convert the performance time from centiseconds to minutes:seconds.hundredths of a
    second (MM:SS.cc format).
    """
    minutes, remainder = divmod(cs, 6000)
    seconds, hundredths = divmod(remainder, 100)
    if minutes > 0:
        return f"{minutes}:{seconds:02d}.{hundredths:02d}"
    return f"{seconds:02d}.{hundredths:02d}"


def time_to_cs(time_str):
    """
    Convert time from MM:SS.cc format to centiseconds.
    """
    try:
        if ":" in time_str:
            minutes_part, rest = time_str.split(":")
            seconds_part, hundredths_part = rest.split(".")
            cs = (
                int(minutes_part) * 6000
                + int(seconds_part) * 100
                + int(hundredths_part)
            )
            return cs
        seconds_part, hundredths_part = time_str.split(".")
        cs = int(seconds_part) * 100 + int(hundredths_part)
        return cs
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid time format '{time_str}'. Use SS.cc or MM:SS.cc "
            "(e.g. 28.74 for 28 seconds and 74 hundredths of a second "
            "or 1:03.12 for 1 minute, 3 seconds and 12 hundredths of a second)."
            " Centiseconds must always be exactly 2 digits (e.g. 28.70 not 27.7)."
        )


# Meets
def add_meet(name, date_start, country_id, date_end=None, location=None, notes=None):
    """
    Add a meet to the meets table.
    """
    meet = (name, date_start, country_id, date_end, location, notes)
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO meets (name, date_start, country_id, date_end, location,
        notes) VALUES (?, ?, ?, ?, ?, ?)""",
            meet,
        )
        return cursor.lastrowid


def list_meets():
    """
    List all meets ordered by date_start descending (most recent first).
    """
    with get_connection() as conn:
        listing = conn.execute(
            """SELECT * FROM meets ORDER BY date_start DESC"""
        ).fetchall()
        return listing


# Swimmers
def add_swimmer(name, date_of_birth, gender, club_id, country_id):
    """
    Add a swimmer to the swimmers table.
    """
    swimmer = (name, date_of_birth, gender, club_id, country_id)
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO swimmers (name, date_of_birth, gender, club_id, country_id)
        VALUES (?, ?, ?, ?, ?)""",
            swimmer,
        )
        return cursor.lastrowid


def add_club(name, country_id):
    """
    Add a club to the clubs table.
    """
    club = (name, country_id)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO clubs (name, country_id) VALUES (?, ?)", club,
        )
        return cursor.lastrowid


def list_swimmers():
    """
    List all swimmers ordered by name.
    """
    with get_connection() as conn:
        listing = conn.execute("""
            SELECT swimmers.id, swimmers.name, swimmers.date_of_birth,
                   swimmers.gender, clubs.name AS club, countries.name AS nationality
            FROM swimmers
            JOIN clubs ON swimmers.club_id = clubs.id
            JOIN countries ON swimmers.country_id = countries.id
            ORDER BY swimmers.name
            """).fetchall()
        return listing


# Performances
def add_performance_metres(
    swimmer_id, meet_id, discipline_metres_id, time_cs, date, session=None,
    is_relay_leg=0, leg_number=None, is_mixed_mf=0, notes=None
):
    """
    Add a swimmer's performance to the performances_metres table.
    """
    performance = (
        swimmer_id,
        meet_id,
        discipline_metres_id,
        time_cs,
        date,
        session,
        is_relay_leg,
        leg_number,
        is_mixed_mf,
        notes,
    )
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO performances_metres (swimmer_id, meet_id,
            discipline_metres_id, time_cs, date, session, is_relay_leg, leg_number,
            is_mixed_mf, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            performance,
        )
        return cursor.lastrowid


def add_performance_yards(
    swimmer_id, meet_id, discipline_yards_id, time_cs, date, session=None,
    is_relay_leg=0, leg_number=None, is_mixed_mf=0, notes=None
):
    """
    Add a swimmer's performance to the performances_yards table.
    """
    performance = (
        swimmer_id,
        meet_id,
        discipline_yards_id,
        time_cs,
        date,
        session,
        is_relay_leg,
        leg_number,
        is_mixed_mf,
        notes,
    )
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO performances_yards (swimmer_id, meet_id,
            discipline_yards_id, time_cs, date, session, is_relay_leg, leg_number,
            is_mixed_mf, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            performance,
        )
        return cursor.lastrowid


def list_performances_metres(swimmer_id=None, discipline_metres_id=None, year=None):
    """
    List a swimmers' performances in a 25, 33 and 50 metres pool.  Possibility to
    filter by swimmer, discipline and year.
    """
    with get_connection() as conn:
        query = """
        SELECT swimmers.name AS swimmer, meets.name AS meet, meets.date_start,
        disciplines_metres.name AS discipline, performances_metres.time_cs,
        performances_metres.date, performances_metres.session, performances_metres.notes
        FROM performances_metres
        JOIN swimmers ON performances_metres.swimmer_id = swimmers.id
        JOIN meets ON performances_metres.meet_id = meets.id
        JOIN disciplines_metres ON performances_metres.discipline_metres_id =
        disciplines_metres.id
        WHERE 1=1
        """
        params = []
        if swimmer_id is not None:
            query += " AND performances_metres.swimmer_id = ?"
            params.append(swimmer_id)
        if discipline_metres_id is not None:
            query += " AND performances_metres.discipline_metres_id = ?"
            params.append(discipline_metres_id)
        if year is not None:
            query += " AND strftime('%Y', performances_metres.date) = ?"
            params.append(str(year))
        query += " ORDER BY performances_metres.date DESC"
        listing = conn.execute(query, params).fetchall()
        return listing


def list_all_performances_metres():
    """
    List all swimmers' performances in all metre sized pools.  No filter options.
    """
    with get_connection() as conn:
        query = """
        SELECT swimmers.name AS swimmer, pools.name AS pool, meets.name AS meet,
        meets.date_start,
        disciplines_metres.name AS discipline, performances_metres.time_cs,
        performances_metres.date, performances_metres.session, performances_metres.notes
        FROM performances_metres
        JOIN swimmers ON performances_metres.swimmer_id = swimmers.id
        JOIN meets ON performances_metres.meet_id = meets.id
        JOIN disciplines_metres ON performances_metres.discipline_metres_id =
        disciplines_metres.id
        JOIN pools ON disciplines_metres.pool_id = pools.id
        ORDER BY swimmers.name, performances_metres.date DESC
        """
        listing = conn.execute(query).fetchall()
        return listing


def list_performances_yards(swimmer_id=None, discipline_yards_id=None, year=None):
    """
    List a swimmers' performances in a 25 yards pool. Possibility to filter by
    swimmer, discipline and year.
    """
    with get_connection() as conn:
        query = """
        SELECT swimmers.name AS swimmer, meets.name AS meet, meets.date_start,
        disciplines_yards.name AS discipline, performances_yards.time_cs,
        performances_yards.date, performances_yards.session, performances_yards.notes
        FROM performances_yards
        JOIN swimmers ON performances_yards.swimmer_id = swimmers.id
        JOIN meets ON performances_yards.meet_id = meets.id
        JOIN disciplines_yards ON performances_yards.discipline_yards_id =
        disciplines_yards.id
        WHERE 1=1
        """
        params = []
        if swimmer_id is not None:
            query += " AND performances_yards.swimmer_id = ?"
            params.append(swimmer_id)
        if discipline_yards_id is not None:
            query += " AND performances_yards.discipline_yards_id = ?"
            params.append(discipline_yards_id)
        if year is not None:
            query += " AND strftime('%Y', performances_yards.date) = ?"
            params.append(str(year))
        query += " ORDER BY performances_yards.date DESC"
        listing = conn.execute(query, params).fetchall()
        return listing


def list_all_performances_yards():
    """
    List all swimmers' performances in a 25 yards pool.  No filter options.
    """
    with get_connection() as conn:
        query = """
        SELECT swimmers.name AS swimmer, meets.name AS meet, meets.date_start,
        disciplines_yards.name AS discipline, performances_yards.time_cs,
        performances_yards.date, performances_yards.session, performances_yards.notes
        FROM performances_yards
        JOIN swimmers ON performances_yards.swimmer_id = swimmers.id
        JOIN meets ON performances_yards.meet_id = meets.id
        JOIN disciplines_yards ON performances_yards.discipline_yards_id =
        disciplines_yards.id
        ORDER BY swimmers.name, performances_yards.date DESC
        """
        listing = conn.execute(query).fetchall()
        return listing


def get_personal_bests_metres(swimmer_id=None, discipline_metres_id=None, pool_id=None):
    """
    Return swimmers' best performances in a 25, 33 and 50m pool.  Possibility to filter
    by swimmer, discipline and pool size.
    """
    with get_connection() as conn:
        query = """
        SELECT
            disciplines_metres.name AS discipline,
            MIN(performances_metres.time_cs) AS best_cs,
            pools.name AS pool,
            performances_metres.date AS date
        FROM performances_metres
        JOIN disciplines_metres ON
        performances_metres.discipline_metres_id = disciplines_metres.id
        JOIN pools ON disciplines_metres.pool_id = pools.id
        WHERE 1=1
        """
        params = []
        if swimmer_id is not None:
            query += " AND performances_metres.swimmer_id = ?"
            params.append(swimmer_id)
        if discipline_metres_id is not None:
            query += " AND performances_metres.discipline_metres_id = ?"
            params.append(discipline_metres_id)
        if pool_id is not None:
            query += " AND disciplines_metres.pool_id = ?"
            params.append(pool_id)
        query += " GROUP BY performances_metres.discipline_metres_id"
        query += " ORDER BY pools.name, disciplines_metres.name"
        personal_bests = conn.execute(query, params).fetchall()
        return personal_bests


def get_all_personal_bests_metres():
    """
    Return all swimmers' best performances in a metre sized pool.
    No filtering options.
    """
    with get_connection() as conn:
        query = """
        SELECT
            swimmers.name AS swimmer,
            disciplines_metres.name AS discipline,
            MIN(performances_metres.time_cs) AS best_cs,
            pools.name AS pool,
            performances_metres.date AS date
        FROM performances_metres
        JOIN swimmers ON performances_metres.swimmer_id = swimmers.id
        JOIN disciplines_metres ON
        performances_metres.discipline_metres_id = disciplines_metres.id
        JOIN pools ON disciplines_metres.pool_id = pools.id
        GROUP BY performances_metres.swimmer_id,
            performances_metres.discipline_metres_id
        ORDER BY swimmers.name, pools.name, disciplines_metres.name
        """
        all_personal_bests = conn.execute(query).fetchall()
        return all_personal_bests


def get_personal_bests_yards(swimmer_id=None, discipline_yards_id=None):
    """
    Return swimmers' best performances in a 25 yards pool.  Possibility to filter
    by swimmer and discipline.
    """
    with get_connection() as conn:
        query = """
        SELECT
            disciplines_yards.name AS discipline,
            MIN(performances_yards.time_cs) AS best_cs,
            performances_yards.date AS date
        FROM performances_yards
        JOIN disciplines_yards ON
        performances_yards.discipline_yards_id = disciplines_yards.id
        WHERE 1=1
        """
        params = []
        if swimmer_id is not None:
            query += " AND performances_yards.swimmer_id = ?"
            params.append(swimmer_id)
        if discipline_yards_id is not None:
            query += " AND performances_yards.discipline_yards_id = ?"
            params.append(discipline_yards_id)
        query += " GROUP BY performances_yards.discipline_yards_id"
        query += " ORDER BY disciplines_yards.name"
        personal_bests = conn.execute(query, params).fetchall()
        return personal_bests


def get_all_personal_bests_yards():
    """
    Return all swimmers' best performances in a 25 yards pool.
    No filtering options.
    """
    with get_connection() as conn:
        query = """
        SELECT
            swimmers.name AS swimmer,
            disciplines_yards.name AS discipline,
            MIN(performances_yards.time_cs) AS best_cs,
            performances_yards.date AS date
        FROM performances_yards
        JOIN swimmers ON performances_yards.swimmer_id = swimmers.id
        JOIN disciplines_yards ON
        performances_yards.discipline_yards_id = disciplines_yards.id
        GROUP BY performances_yards.swimmer_id,
            performances_yards.discipline_yards_id
        ORDER BY swimmers.name, disciplines_yards.name
        """
        all_personal_bests = conn.execute(query).fetchall()
        return all_personal_bests


def get_performance_by_time_metres(swimmer_id, discipline_metres_id, time_cs):
    """
    Retrieve the full performance row(s) for a specific time in a metres pool.
    Used to get meet, session and notes for a personal best.
    Multiple rows may be returned if the same time was achieved twice.
    """
    with get_connection() as conn:
        query = """
            SELECT
                performances_metres.time_cs,
                performances_metres.date,
                performances_metres.session,
                performances_metres.notes,
                meets.name AS meet,
                disciplines_metres.name AS discipline
            FROM performances_metres
            JOIN meets ON performances_metres.meet_id = meets.id
            JOIN disciplines_metres ON performances_metres.discipline_metres_id =
                disciplines_metres.id
            WHERE performances_metres.swimmer_id = ?
            AND performances_metres.discipline_metres_id = ?
            AND performances_metres.time_cs = ?
        """
        return conn.execute(
            query, (swimmer_id, discipline_metres_id, time_cs)
        ).fetchall()


def get_performance_by_time_yards(swimmer_id, discipline_yards_id, time_cs):
    """
    Retrieve the full performance row(s) for a specific time in a yards pool.
    Used to get meet, session and notes for a personal best.
    Multiple rows may be returned if the same time was achieved twice.
    """
    with get_connection() as conn:
        query = """
            SELECT
                performances_yards.time_cs,
                performances_yards.date,
                performances_yards.session,
                performances_yards.notes,
                meets.name AS meet,
                disciplines_yards.name AS discipline
            FROM performances_yards
            JOIN meets ON performances_yards.meet_id = meets.id
            JOIN disciplines_yards ON performances_yards.discipline_yards_id =
                disciplines_yards.id
            WHERE performances_yards.swimmer_id = ?
            AND performances_yards.discipline_yards_id = ?
            AND performances_yards.time_cs = ?
        """
        return conn.execute(
            query, (swimmer_id, discipline_yards_id, time_cs)
        ).fetchall()


# Lookup functions for cli.py
def list_countries():
    """
    List all countries ordered by their full name.
    """
    with get_connection() as conn:
        query = """
        SELECT *
        FROM countries
        ORDER BY name
        """
        listing = conn.execute(query).fetchall()
        return listing


def list_clubs():
    """
    List all clubs ordered by their full name.
    """
    with get_connection() as conn:
        query = """
        SELECT *
        FROM clubs
        ORDER BY name
        """
        listing = conn.execute(query).fetchall()
        return listing


def list_disciplines_metres():
    """
    List all disciplines in pool sizes 25, 33 and 50 metres, ordered by their full name.
    """
    with get_connection() as conn:
        query = """
        SELECT *
        FROM disciplines_metres
        ORDER BY name
        """
        listing = conn.execute(query).fetchall()
        return listing


def list_disciplines_yards():
    """
    List all disciplines in a 25 yards pool, ordered by their full name.
    """
    with get_connection() as conn:
        query = """
        SELECT *
        FROM disciplines_yards
        ORDER BY name
        """
        listing = conn.execute(query).fetchall()
        return listing


def list_pools_metres():
    """
    List all pool sizes in metres.
    """
    with get_connection() as conn:
        query = """
        SELECT *
        FROM pools
        WHERE unit = 'metres'
        ORDER BY id
        """
        listing = conn.execute(query).fetchall()
        return listing
