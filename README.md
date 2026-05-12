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
events (Freestyle, Backstroke, Breaststroke, Butterfly, Individual Medley)
in both 25m and 50m pools, plus relay events.

## Database schema

SwimSQL uses a local SQLite database with the following structure:

| Table | Description |
|---|---|
| `countries` | Reference table of countries (ISO 3166-1 alpha-3 codes) |
| `clubs` | Swimming clubs, linked to a country |
| `swimmers` | Swimmers, linked to a club and a nationality |
| `pools` | Pool types (length and unit: metres or yards) |
| `disciplines` | Events (stroke, distance, pool type), pre-seeded at first run |
| `meets` | Competitions (name, date, location, country) |
| `performances` | Results linking a swimmer, discipline, meet and time (performance) |

### Relationships

```
countries <-- clubs <-- swimmers --> countries
                             |
                        performances --> meets --> countries
                             |
                        disciplines --> pools
```

## Requirements

- Python 3.10 or higher
- [tabulate](https://pypi.org/project/tabulate/) — terminal table formatting
- [openpyxl](https://pypi.org/project/openpyxl/) — XLSX export
- [odfpy](https://pypi.org/project/odfpy/) — ODS export

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
~/.swimsql/swimsql.db

This folder is created automatically on first run. To back up your data,
copy this file to a safe location. To migrate to a new machine, copy it
to the same path on the new machine.

## License

The SwimSQL project is licensed under the
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

You are free to use, modify, and distribute this software, provided that
any modifications to the original files are released under the same licence.
