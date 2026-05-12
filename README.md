# swimsql

A command-line tool for tracking swimming competition performances,
built with Python and SQLite.

## What it does

swimsql lets you record and consult a swimmer's competition results
from the terminal. No internet connection, no account, no server — just
a local database on your machine.

**Features:**
- Record meets and performances by discipline
- Filter results by discipline and year
- View personal bests across all disciplines
- Export results to ODS and XLSX for sharing (e.g. via Nextcloud/Collabora)

Disciplines are pre-loaded at first run and cover all standard individual
events (Freestyle, Backstroke, Breaststroke, Butterfly, Individual Medley)
in both 25m and 50m pools, plus relay events.

## Requirements

- Python 3.10 or higher
[to be completed]

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


## License

This project is licensed under the
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

You are free to use, modify, and distribute this software, provided that
any modifications to the original files are released under the same licence.
