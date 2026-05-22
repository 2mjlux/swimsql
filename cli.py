# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# http://mozilla.org/MPL/2.0/.
# Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)

import db
import sys
from tabulate import tabulate


# Helper functions
def prompt(label, optional=False):
    """
    Ask the user for a single line of input.
    Returns None if optional and user pressed Enter without typing.
    """
    if optional:
        value = input(f"{label} (optional, press Enter to skip): ").strip()
    else:
        value = input(f"{label}: ").strip()
    return value if value else None


def prompt_date(label, optional=False):
    """
    Ask the user for a date in YYYY-MM-DD format.
    Returns None if optional and user pressed Enter without typing.
    """
    while True:
        if optional:
            date = input(
                f"{label} (YYYY-MM-DD, optional - press Enter to skip):"
            ).strip()
            if not date:
                return None
        else:
            date = input(f"{label} (YYYY-MM-DD): ").strip()
        if (
            len(date) == 10
            and date[0:4].isdigit()
            and date[4] == "-"
            and date[5:7].isdigit()
            and date[7] == "-"
            and date[8:10].isdigit()
        ):
            return date
        print(" Invalid date format. Please use YYYY-MM-DD (e.g. 2026-05-20).")


def confirm(question):
    """
    Asks the user a yes/no question.  True means yes and False means no.
    """
    answer = input(f"{question} (y/n): ")
    return answer.lower() == "y"


def select_from_list(items, label_fn, title):
    """
    Display a numbered list and return the item the users picks.
    Returns None if the user cancels with 0.
    """
    print(title)
    for i, item in enumerate(items, start=1):
        print(f"  {i}. {label_fn(item)}")
    print("  0. Cancel")
    while True:
        choice = input("Enter number: ").strip()
        if choice == "0":
            return None  # selection cancelled
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("  Invalid choice, please try again.")


def search_from_list(items, label_fn, title):
    """
    Display a filtered list of items corresponding to the first letter(s) typed by the
    user.  Return the item the user picks.  Returns None if the user cancels with 0."
    """
    print(title)
    print("  0. Cancel")
    while True:
        search = input("Enter the first letter(s): ").strip().lower()
        if search == "0":
            return None  # selection cancelled
        filtered = [item for item in items if search in label_fn(item).lower()]
        if not filtered:
            print("No item starting with the letter(s) typed. Try again.")
        elif len(filtered) == 1:
            return filtered[0]
        else:
            return select_from_list(filtered, label_fn, title)


def select_discipline_metres():
    """
    Guide the user through selecting a metres discipline via sub-menus.
    Steps: pool -> stroke -> distance -> individual/relay (if applicable).
    Return a disciplines_metres row or None if cancelled.
    """

    # Pick a pool
    pools = db.list_pools_metres()
    pool = select_from_list(pools, lambda p: p["name"], "Select pool size")
    if pool is None:
        return None  # selection cancelled

    # Pick a stroke
    disciplines = db.list_disciplines_metres()
    pool_disciplines = [d for d in disciplines if d["pool_id"] == pool["id"]]
    strokes = sorted(set(d["stroke"] for d in pool_disciplines))
    stroke = select_from_list(strokes, lambda s: s, "Select stroke")
    if stroke is None:
        return None  # selection cancelled

    # Pick a distance
    stroke_disciplines = [d for d in pool_disciplines if d["stroke"] == stroke]
    distances = sorted(set(d["distance"] for d in stroke_disciplines))
    distance = select_from_list(distances, lambda d: f"{d}m", "Select distance")
    if distance is None:
        return None  # selection cancelled

    # Check Individual or Relay
    ultimate = [d for d in stroke_disciplines if d["distance"] == distance]
    if len(ultimate) == 1:
        return ultimate[0]  # only one option, no need to ask
    options = ["Individual", "Relay"]
    selection = select_from_list(options, lambda o: o, "Individual or Relay?")
    if selection is None:
        return None  # selection cancelled
    individual = [d for d in ultimate if d["is_relay"] == 0]
    relay = [d for d in ultimate if d["is_relay"] == 1]
    return individual[0] if selection == "Individual" else relay[0]


def select_discipline_yards():
    """
    Guide the user through selecting a yards discipline via sub-menus.
    Steps: stroke -> distance -> individual/relay (if applicable).
    Return a disciplines_yards row or None if cancelled.
    """

    # Pick a stroke
    disciplines = db.list_disciplines_yards()
    strokes = sorted(set(d["stroke"] for d in disciplines))
    stroke = select_from_list(strokes, lambda s: s, "Select stroke")
    if stroke is None:
        return None  # selection cancelled

    # Pick a distance
    stroke_disciplines = [d for d in disciplines if d["stroke"] == stroke]
    distances = sorted(set(d["distance"] for d in stroke_disciplines))
    distance = select_from_list(distances, lambda d: f"{d}y", "Select distance")
    if distance is None:
        return None  # selection cancelled

    # Check Individual or Relay
    ultimate = [d for d in stroke_disciplines if d["distance"] == distance]
    if len(ultimate) == 1:
        return ultimate[0]  # only one option, no need to ask
    options = ["Individual", "Relay"]
    selection = select_from_list(options, lambda o: o, "Individual or Relay?")
    if selection is None:
        return None  # selection cancelled
    individual = [d for d in ultimate if d["is_relay"] == 0]
    relay = [d for d in ultimate if d["is_relay"] == 1]
    return individual[0] if selection == "Individual" else relay[0]


# Flow functions
def flow_add_meet():
    """
    Function for the user to add a Meet.
    """
    print("--- Add Meet ---")
    while True:
        name = prompt("Name of Meet")
        if name:
            break
        print("  Meet name is required.")
    date_start = prompt_date("Start date")
    date_end = prompt_date("End date", optional=True)
    location = prompt("Location", optional=True)
    country = search_from_list(
        db.list_countries(), lambda c: c["name"], "Select country"
    )
    if country is None:
        return
    country_id = country["id"]
    notes = prompt("Notes", optional=True)
    db.add_meet(name, date_start, country_id, date_end, location, notes)
    print(f"  Meet '{name}' successfully added!")


def flow_add_swimmer():
    """
    Function for the user to add a swimmer.
    """
    print("--- Add Swimmer ---")
    while True:
        name = prompt("Name of swimmer")
        if name:
            break
        print("  Swimmer's name is required.")
    date_of_birth = prompt_date("Date of birth")
    while True:
        gender = prompt("Gender of swimmer (enter M or F)")
        if gender and gender.upper() in ("M", "F"):
            gender = gender.upper()
            break
        print("  Please enter M or F.")
    club = search_from_list(db.list_clubs(), lambda cl: cl["name"], "Select club")
    if club is None:
        return
    club_id = club["id"]
    country = search_from_list(
        db.list_countries(), lambda c: c["name"], "Select country (nationality)"
    )
    if country is None:
        return
    country_id = country["id"]
    db.add_swimmer(name, date_of_birth, gender, club_id, country_id)
    print(f"  Swimmer '{name}' successfully added!")


def flow_add_performance():
    """
    Function for the user to add a swimmer's performance.
    """
    print("--- Add Performance ---")
    swimmer = search_from_list(
        db.list_swimmers(), lambda s: s["name"], "Select swimmer"
    )
    if swimmer is None:
        return
    swimmer_id = swimmer["id"]
    units = ["Metres", "Yards"]
    unit = select_from_list(
        units, lambda u: u, "Select Metres or Yards"
    )
    if unit is None:
        return
    if unit == "Metres":
        discipline = select_discipline_metres()
        if discipline is None:
            return
        discipline_metres_id = discipline["id"]
    else:
        discipline = select_discipline_yards()
        if discipline is None:
            return
        discipline_yards_id = discipline["id"]
    meet = search_from_list(
        db.list_meets(), lambda m: f"{m['date_start']} - {m['name']}", "Select Meet"
    )
    if meet is None:
        return
    meet_id = meet["id"]
    date = prompt_date("Date of performance")
    session = None
    if confirm("Add session (AM/PM)?"):
        sessions = ["AM", "PM"]
        session = select_from_list(
            sessions, lambda s: s, "Select 'AM' (morning) or 'PM' (afternoon/evening)"
        )
    while True:
        time_str = prompt("Enter time in MM:SS.cc format (minutes:seconds.centiseconds), e.g. 30.05 or 1:01.56")
        if time_str is None:
            print("  Time is required.")
            continue
        try:
            time_cs = db.time_to_cs(time_str)
            break
        except ValueError as e:
            print(f"  {e}")
    notes = prompt("Here you can enter your notes", optional=True)
    if unit == "Metres":
        db.add_performance_metres(
            swimmer_id, meet_id, discipline_metres_id, time_cs, date, session, notes
        )
    else:
        db.add_performance_yards(
            swimmer_id, meet_id, discipline_yards_id, time_cs, date, session, notes
        )
    print(f"  Performance {time_str} successfully added!")
