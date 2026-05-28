# SwimSQL

> ⚠️ This project is currently under active development and is not yet functional.
> `db.py` is complete. `cli.py` is nearly complete. `export.py` and `swimsql.py` are pending.

A command-line tool for tracking swimming competition performances,
built with Python and SQLite.


## What it does

SwimSQL lets you record and consult a swimmer's competition results
from the terminal. No internet connection, no account, no server - just
a local database on your machine.

**Features:**
- Record meets and performances by discipline
- Filter results by discipline and year
- View personal bests across all disciplines
- Export results to ODS or XLSX for sharing

Disciplines are pre-loaded at first run and cover all standard individual
events (Freestyle, Backstroke, Breaststroke, Butterfly, Medley)
in 25m, 50m, and 33m metre pools and 25y yard pools, plus relay events.


## Architecture

SwimSQL follows a strict separation of responsibilities across its modules:

| Module | Responsibility |
|---|---|
| `db.py` | All database interaction: SQL queries, inserts, schema creation, seeding |
| `cli.py` | All user interaction: menus, prompts, input validation |
| `export.py` | Export of results to ODS and XLSX formats |
| `swimsql.py` | Entry point: launches the application |

No SQL is written outside `db.py`. No user interaction happens outside `cli.py`.
The modules communicate in one direction only:

```
swimsql.py --> cli.py --> db.py --> swimsql.db
                     --> export.py --> swimsql.ods / swimsql.xlsx
```

### cli.py in detail

`cli.py` contains three types of functions:

**Helper functions** — reusable building blocks:
- `prompt()` — ask the user for a single input
- `prompt_date()` — ask the user for a date in YYYY-MM-DD format
- `prompt_year()` — ask the user for a year in YYYY format
- `select_from_list()` — show a numbered list, return the chosen item
- `search_from_list()` — search a long list by typing first letters
- `confirm()` — ask a yes/no question
- `select_discipline_metres()` — guided sub-menu for picking a metres discipline
- `select_discipline_yards()` — guided sub-menu for picking a yards discipline

**Flow functions** — one per menu option:
- `flow_add_meet()` — prompts for meet details, calls `add_meet()` from `db.py`
- `flow_add_swimmer()` — prompts for swimmer details, calls `add_swimmer()` from `db.py`
- `flow_add_club()` — prompts for club details, calls `add_club()` from `db.py`
- `flow_add_performance()` — prompts for performance, calls `add_performance_metres()` or `add_performance_yards()` from `db.py`
- `flow_list_performances()` — asks for filters, displays results via tabulate
- `flow_personal_bests()` — displays personal bests via tabulate
- `flow_export()` — generates ODS/XLSX file via `export.py`

**Main menu** — the `main()` function that ties everything together.

### Key principle

`cli.py` never writes SQL. `db.py` never asks the user anything.
They communicate in one direction:
```
cli.py collects input --> calls db.py functions --> db.py returns data --> cli.py displays it
```


### export.py in detail

`export.py` generates a complete snapshot of the database in ODS or XLSX
format. The export contains four sheets:

| Sheet | Contents |
|---|---|
| `Performances Metres` | All swimmers' metre-based performances |
| `Performances Yards` | All swimmers' yard-based performances |
| `Personal Bests Metres` | Best time per swimmer per metre discipline |
| `Personal Bests Yards` | Best time per swimmer per yard discipline |

Family members can filter and sort the data using Collabora Online,
LibreOffice, OpenOffice, or Excel.


## Database schema

SwimSQL uses a local SQLite database with the following structure:

| Table | Description |
|---|---|
| `countries` | Reference table of countries (ISO 3166-1 alpha-3 codes) |
| `clubs` | Swimming clubs, linked to a country |
| `swimmers` | Swimmers, linked to a club and a nationality |
| `pools` | Pool types (length and unit: metres or yards) |
| `disciplines_metres` | Metre-based events (stroke, distance, pool), pre-seeded at first run |
| `disciplines_yards` | Yard-based events (stroke, distance), pre-seeded at first run |
| `meets` | Competitions (name, start and end date, location, country) |
| `performances_metres` | Metre-based results linking swimmer, discipline, meet, date, session and time |
| `performances_yards` | Yard-based results linking swimmer, discipline, meet, date, session and time |
| `relay_legs_metres` | Individual leg times within a metre-based relay |
| `relay_legs_yards` | Individual leg times within a yard-based relay |

### Notes

- Times are stored as integers in **centiseconds** (hundredths of a second).
  A time of 1:23.45 is stored as 8345.
- Metres and yards events are stored in separate tables as they represent
  different measurement systems with different standard distances.
- Relay leg times record `start_type` (standing or flying) and `is_mixed_mf`
  to determine whether a split time is eligible for individual records.

### Relationships (diagram)

```
pools <-- disciplines_metres <-- performances_metres --> meets --> countries
          disciplines_yards  <-- performances_yards  --> meets --> countries
                                        |
                      countries <-- swimmers --> clubs --> countries
                                        |
                             +----------+----------+
                             |                     |
                    relay_legs_metres       relay_legs_yards
```

### Relationships (prose)

- `clubs` belong to a `country`
- `swimmers` belong to a `club` and have a `country` (nationality)
- `disciplines_metres` reference a `pool`
- `disciplines_yards` reference no pool (25y is the only yards pool)
- `performances_metres` link a `swimmer`, `discipline_metres`, and `meet`
- `performances_yards` link a `swimmer`, `discipline_yards`, and `meet`
- `meets` take place in a `country`
- `relay_legs_metres` link individual leg times to a `performances_metres` team result and a `swimmer`
- `relay_legs_yards` link individual leg times to a `performances_yards` team result and a `swimmer`

### Additional detail relay leg fields

Each relay leg records:
- `leg_number`  -- position in the relay (1, 2, 3 or 4)
- `stroke`      -- stroke swum (especially important for medley relays)
- `time_cs`     -- individual leg time in centiseconds
- `start_type`  -- 'standing' (leg 1) or 'flying' (legs 2, 3, 4)
- `is_mixed_mf` -- 1 if mixed gender relay (split times cannot count for records)


## Requirements

- Python 3.10 or higher
- [tabulate](https://pypi.org/project/tabulate/) — terminal table formatting
- [odfpy](https://pypi.org/project/odfpy/) — ODS export
- [openpyxl](https://pypi.org/project/openpyxl/) — XLSX export
- [pycountry](https://pypi.org/project/pycountry/) — ISO country codes

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

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python swimsql.py
```

You will be presented with a menu:

[to be completed]

### Data storage

SwimSQL stores its database at `~/.swimsql/swimsql.db`. This folder is
created automatically on first run. To back up your data, copy this file
to a safe location. To migrate to a new machine, copy it to the same path
on the new machine.


## License

The SwimSQL project is licensed under the
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

You are free to use, modify, and distribute this software, provided that
any modifications to the original files are released under the same licence.

Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)
