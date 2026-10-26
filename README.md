# SwimSQL

> SwimSQL v1.1.0 is released: editing and deleting are now supported. 61 automated tests, 100% code coverage of the database layer.

A command-line tool for tracking swimming competition performances, built with Python and SQLite.


## What it does

SwimSQL lets you record and consult a swimmer's competition results from the terminal. No internet connection, no account, no server - just a local database on your machine. Multiple swimmers can be recorded in the database.

**Features:**
- Record meets and performances by discipline
- Record relay team results and individual relay leg times
- Optionally record points associated with the performance
- Filter results by discipline and year
- View personal bests across all individual disciplines
- Edit clubs, swimmers, meets and performances
- Delete clubs, swimmers, meets and performances, with safeguards against orphaned data
- Export results to ODS or XLSX for sharing

Disciplines are pre-loaded at first run and cover all standard individual events (Butterfly, Backstroke, Breaststroke, Freestyle, Medley) in 25, 50, and 33 metre pools and the 25 yard pool, plus relay events.


## Architecture

SwimSQL follows a strict separation of responsibilities across its modules:

| Module | Responsibility |
|---|---|
| `db.py` | All database interaction: SQL queries, inserts, updates, deletes, schema creation, seeding |
| `cli.py` | All user interaction: menus, prompts, input validation |
| `export.py` | Export of results to ODS and XLSX formats |
| `swimsql.py` | Entry point: launches the application |

No SQL is written outside `db.py`. No user interaction happens outside `cli.py`.
The modules communicate in a strict hierarchy:

```
swimsql.py
    │
    └── cli.py ──────────────────── db.py ── swimsql.db
            │                         │
            └────── export.py ────────┘
                         │
                         └── swimsql.ods / swimsql.xlsx
```

### cli.py in a nutshell

`cli.py` contains two types of functions:

- **Helper functions**, which are reusable building blocks
- **Flow functions**, one per menu option

The `main()` function in `swimsql.py` ties everything together.

### Key principle

`cli.py` never writes SQL. `db.py` never asks the user anything.
They communicate in one direction:
```
cli.py collects input --> calls db.py functions --> db.py returns data --> cli.py displays it
```

### Deletion safeguards

Deletion is permanent, so `db.py` refuses any deletion that would leave other entries pointing at nothing:

| Deleting a... | Refused while... |
|---|---|
| club | swimmers are members of it |
| swimmer | performances are linked to them |
| meet | performances are linked to it |
| performance | never refused - nothing depends on a performance |

`cli.py` checks the same condition before asking for confirmation, so the user is never asked to confirm a deletion that cannot happen. The check in `db.py` remains as a safety net.


### export.py in a nutshell

`export.py` generates a complete snapshot of the database in ODS or XLSX
format. The export contains four sheets:

| Sheet | Contents |
|---|---|
| `Performances Metres` | All swimmers' metre-based performances |
| `Performances Yards` | All swimmers' yard-based performances |
| `Personal Bests Metres` | Best time per swimmer per metre discipline |
| `Personal Bests Yards` | Best time per swimmer per yard discipline |

Athletes, family and friends can filter and sort the data using Collabora Online, LibreOffice, OpenOffice, or Excel.

Relay leg times are labelled in the export: a leg shows for example as `4x50m Medley Relay (leg 1)`, a team result shows the plain discipline name.


## Database schema

SwimSQL uses a local SQLite database with the following structure:

| Table | Description |
|---|---|
| `countries` | Reference table of countries (ISO 3166-1 alpha-3 codes) |
| `clubs` | Swimming clubs, linked to a country |
| `swimmers` | Swimmers (first, middle, last name), linked to a club and a nationality |
| `pools` | Pool types (length and unit: metres or yards) |
| `disciplines_metres` | Metre-based events (stroke, distance, pool), pre-seeded at first run |
| `disciplines_yards` | Yard-based events (stroke, distance), pre-seeded at first run |
| `meets` | Competitions (name, start and end date, location, country) |
| `performances_metres` | Metre-based results linking swimmer, discipline, meet, date, session, time and optional relay leg details |
| `performances_yards` | Yard-based results linking swimmer, discipline, meet, date, session, time and optional relay leg details |

### Notes

- Times are stored as integers in **centiseconds** (hundredths of a second). A time of 1:23.45 is stored as 8345.
- Metres and yards events are stored in separate tables as they represent different measurement systems with different standard distances.
- Individual relay leg times are recorded directly in `performances_metres` and `performances_yards` with `is_relay_leg`, `leg_number` and `is_mixed_mf` fields. Relay legs are displayed with the leg number (and possibly `mixed` for a mixed relay) in brackets, e.g. `4x50m Medley Relay (leg 1, mixed)`.

### Relationships (diagram)

```
pools <-- disciplines_metres <-- performances_metres --> meets --> countries
          disciplines_yards  <-- performances_yards  --> meets --> countries
                                        |
                      countries <-- swimmers --> clubs --> countries
```

### Relationships (prose)

- `clubs` belong to a `country`
- `swimmers` belong to a `club` and have a `country` (nationality)
- `disciplines_metres` reference a `pool`
- `disciplines_yards` reference no pool (25y is the only yards pool)
- `performances_metres` link a `swimmer`, `discipline_metres`, and `meet`
- `performances_yards` link a `swimmer`, `discipline_yards`, and `meet`
- `meets` take place in a `country`

### Relay leg fields in performances tables

When recording an individual relay leg time, the following additional
fields are populated in `performances_metres` or `performances_yards`:

- `is_relay_leg` - 1 if this time was swum during a relay leg
- `leg_number` - position in the relay (1-4); leg 1 = standing start (time may count as individual record), legs 2-4 = flying start (time cannot count for individual records)
- `is_mixed_mf` - 1 if mixed gender relay. Leg 1 of a non-mixed relay may count as an individual record. Leg 1 of a mixed relay cannot count for records under European Aquatics rules. Source: https://europeanaquatics.org/wp-content/uploads/2025/10/GENERAL-EVENT-RULES-sept-2025.pdf


## Known limitations

SwimSQL v1.1.0 supports the full set of create, read, update and delete operations (CRUD) for clubs, swimmers, meets and performances, with the following limitations:

**Editing**
- A performance's swimmer and discipline cannot be edited. To correct either, delete the performance and enter it again.
- An optional field (middle name, notes, session, end date, location) cannot be cleared once it has a value; pressing Enter keeps the current value.

**Input**
- Text prompts (names, dates, times) cannot be cancelled with `0`; only list selections can.
- Dates are checked for format (YYYY-MM-DD) only, so an impossible date such as `2026-02-30` is accepted. A performance's date is not checked against its meet's dates.
- Adding a swimmer with the same name and date of birth as an existing one gives no warning.

**Relays**
- Men's, women's and mixed relays share one discipline per relay event, although they are separate events under World Aquatics rules. Whether a relay was mixed is recorded on each performance instead.
- Relay discipline names do not include the pool size.
- Relay legs are recorded as individual performances and cannot be linked together into a single team result.


## Testing

SwimSQL uses pytest for automated testing of the database layer (`db.py`), which is the most critical module - all data is stored and retrieved there.

### What is tested

- **Time conversion** - `cs_to_time()` and `time_to_cs()` including edge cases (zero, invalid format, invalid centiseconds, None input)
- **Database seeding** - pools, countries, metres and yards disciplines
- **Repeated initialisation** - running `init_db()` on an existing database adds nothing, as happens on every launch after the first
- **Create and read** - meets, clubs, swimmers, performances (metres and yards)
- **Update** - every editable field of clubs, swimmers, meets and performances changed and read back, including empty fields given a value and performances moved to a different meet
- **Delete** - each entry type removed; performance deletion tested with two rows to prove only the selected one is removed
- **Deletion safeguards** - deleting a club with members, a swimmer with performances, or a meet with performances raises an error **and** leaves the entry in place
- **Dependency counts** - counts combine metres and yards performances, and are filtered to the requested club, swimmer or meet
- **Personal bests** - correct fastest time returned across multiple meets, including duplicate times at different meets
- **Filters** - discipline filter and year filter for list functions
- **Relay fields** - `is_relay_leg`, `leg_number`, `is_mixed_mf` stored correctly
- **Points** - stored and retrieved correctly, `None` when not entered
- **Swimmer names** - with and without middle name
- **Data integrity** - foreign key constraints enforced
- **Relay exclusion** - relay disciplines do not appear in personal bests

Each test runs against its own temporary database, so tests never touch real data and cannot affect one another.

### Coverage

61 automated tests covering 100% of `db.py` statements.

`cli.py` and `export.py` are verified through manual end-to-end testing. For v1.1.0, the edit and delete flows were tested path by path: every cancellation point, every deletion refusal, and successful edits and deletions in both metres and yards.

### Running tests

```bash
pytest                                        # run all tests
pytest -v                                     # verbose output
pytest --cov=db --cov-report=term-missing     # with coverage report
```


## Code style

Code is flake8 compliant with a line length of 88 (set in `setup.cfg`).


## Development database

When developing features that modify or delete data, point `DB_PATH` in `db.py` at a separate database so manual testing cannot touch real data:

```python
DB_PATH = Path.home() / ".swimsql" / "swimsql-dev.db"
```

`main()` in `swimsql.py` prints a warning at startup whenever the database filename contains "dev", so you always know which database you are using. **Revert the path before merging.**


## Requirements

- Python 3.10 or higher
- [tabulate](https://pypi.org/project/tabulate/) - terminal table formatting
- [odfpy](https://pypi.org/project/odfpy/) - ODS export
- [openpyxl](https://pypi.org/project/openpyxl/) - XLSX export
- [pycountry](https://pypi.org/project/pycountry/) - ISO country codes

All other dependencies (SQLite, etc.) are included in Python's standard library.


## Installation

Clone the repository:

```bash
git clone https://github.com/2mjlux/swimsql.git
cd swimsql
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install runtime dependencies:

```bash
pip install -r requirements.txt
```

For development and testing, also install:

```bash
pip install -r requirements-dev.txt
```


## Usage

Run the application:

```bash
python swimsql.py
```

You will be presented with a welcome screen followed by the main menu:

```
=== SwimSQL v1.1.0 ===
  1. Add club
  2. Add swimmer
  3. Add meet
  4. Add performance
  5. List performances
  6. Personal bests
  7. Export
  8. Edit
  9. Delete
  L. Lists
  0. Quit
```


### Recording relays

A relay requires two or three separate entries:

**1. The team result**: select the relay discipline, answer `n` to "individual relay leg time?", enter the team's total time and the team's points.

**2. The swimmer's leg**: same discipline and meet, answer `y`, enter the leg number (1-4), whether the relay was mixed, and the swimmer's split time. Legs have no points of their own.

**3. Only for an eligible leg 1**: under European Aquatics rules, a standing-start leg 1 in a non-mixed relay may count as an individual time. To have it compete for a personal best, enter it a third time under the **individual** discipline it was actually swum in (e.g. `50m Backstroke` for the backstroke leg of a medley relay), with a note recording its origin. Legs 2-4 are flying starts and are never eligible.

For medley relays, select `Medley` as the stroke - not the stroke of the leg. Leg order is 1-Backstroke, 2-Breaststroke, 3-Butterfly, 4-Freestyle.


### Personal bests

Personal bests cover individual disciplines only. Relay disciplines are excluded, because a relay group would otherwise mix team totals with individual leg splits and report whichever number happens to be smaller. A leg 1 time that is eligible as an individual record should be entered under its individual discipline (see Recording relays above).


### Data storage and backup

SwimSQL stores its database at `~/.swimsql/swimsql.db`. This folder is created automatically on first run, and the welcome screen shows the exact path on your computer.

All your data lives in that single file. The bash command to back up your database is as follows:

```bash
cp ~/.swimsql/swimsql.db ~/.swimsql/$(date +%Y%m%d)-swimsql-backup.db
```

This creates a dated copy, e.g. `20260903-swimsql-backup.db`. Back up after each data entry session, and always before deleting entries. Keep a copy outside your home directory (external drive, cloud storage).

To restore a backup, close SwimSQL and copy it back:

```bash
cp ~/.swimsql/20260903-swimsql-backup.db ~/.swimsql/swimsql.db
```

To migrate to a new machine, copy the database file to the same path there.


## License

The SwimSQL project is licensed under the [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

You are free to use, modify, and distribute this software, provided that any modifications to the original files are released under the same licence.

Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)
