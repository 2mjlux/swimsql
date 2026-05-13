# SwimSQL

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
- Export results to XLSX or ODS for sharing

Disciplines are pre-loaded at first run and cover all standard individual
events (Freestyle, Backstroke, Breaststroke, Butterfly, Medley)
in 25m, 50m, and 33m metre pools and 25y yard pools, plus relay events.

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

### Notes

- Times are stored as integers in **centiseconds** (hundredths of a second). A time of 1:23.45 is stored as 8345.
- Metres and yards events are stored in separate tables as they represent different measurement systems with different standard distances.

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


## Requirements

- Python 3.10 or higher
- [tabulate](https://pypi.org/project/tabulate/) — terminal table formatting
- [openpyxl](https://pypi.org/project/openpyxl/) — XLSX export
- [odfpy](https://pypi.org/project/odfpy/) — ODS export
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

SwimSQL stores its database at:

```bash
~/.swimsql/swimsql.db
```

This folder is created automatically on first run. To back up your data,
copy this file to a safe location. To migrate to a new machine, copy it
to the same path on the new machine.

## License

The SwimSQL project is licensed under the
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

You are free to use, modify, and distribute this software, provided that
any modifications to the original files are released under the same licence.
