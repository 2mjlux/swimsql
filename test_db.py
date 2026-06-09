# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# http://mozilla.org/MPL/2.0/.
# Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)

# SwimSQL test suite
# Run with: pytest test_db.py -v

import pytest
import tempfile
from pathlib import Path
import db


@pytest.fixture
def test_db(monkeypatch):
    """
    Create a temporary database for testing.
    Overrides DB_PATH so tests never touch the real database.
    Automatically deleted after each test.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    monkeypatch.setattr(db, "DB_PATH", temp_path)
    db.init_db()
    yield
    temp_path.unlink(missing_ok=True)


# --- Time helper tests (no database needed) ---

def test_cs_to_time_seconds_only():
    assert db.cs_to_time(2874) == "28.74"


def test_cs_to_time_with_minutes():
    assert db.cs_to_time(6345) == "1:03.45"


def test_cs_to_time_zero():
    assert db.cs_to_time(0) == "00.00"


def test_time_to_cs_seconds_only():
    assert db.time_to_cs("28.74") == 2874


def test_time_to_cs_with_minutes():
    assert db.time_to_cs("1:03.45") == 6345


def test_time_to_cs_invalid_format():
    with pytest.raises(ValueError):
        db.time_to_cs("abc")


def test_time_to_cs_invalid_centiseconds():
    with pytest.raises(ValueError):
        db.time_to_cs("28.7")


def test_time_to_cs_none():
    with pytest.raises(ValueError, match="Time cannot be None"):
        db.time_to_cs(None)


# --- Seeding tests ---

def test_pools_metres_seeded(test_db):
    pools = db.list_pools_metres()
    assert len(pools) == 3


def test_countries_seeded(test_db):
    countries = db.list_countries()
    assert len(countries) > 0


def test_disciplines_metres_seeded(test_db):
    disciplines = db.list_disciplines_metres()
    assert len(disciplines) > 0


def test_disciplines_yards_seeded(test_db):
    disciplines = db.list_disciplines_yards()
    assert len(disciplines) > 0
