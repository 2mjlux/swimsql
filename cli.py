# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# http://mozilla.org/MPL/2.0/.
# Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)

import db
import export
from tabulate import tabulate
from pathlib import Path
from datetime import datetime


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


def _is_valid_date(value):
    """
    Return True if value is a date in YYYY-MM-DD format.
    """
    return (
        len(value) == 10
        and value[0:4].isdigit()
        and value[4] == "-"
        and value[5:7].isdigit()
        and value[7] == "-"
        and value[8:10].isdigit()
    )


def prompt_keep(label, current):
    """
    Ask for a new value, showing the current one in brackets.
    Returns the current value if the user presses Enter.
    An empty current value is shown as a dash.
    """
    display = current if current is not None else "-"
    value = input(f"{label} [{display}]: ").strip()
    return value if value else current


def prompt_keep_date(label, current):
    """
    Ask for a new date in YYYY-MM-DD format, showing the current one in brackets.
    Returns the current value if the user presses Enter.
    An empty current value is shown as a dash.
    """
    display = current if current is not None else "-"
    while True:
        value = input(f"{label} (YYYY-MM-DD) [{display}]: ").strip()
        if not value:
            return current
        if _is_valid_date(value):
            return value
        print("  Invalid date format. Please use YYYY-MM-DD (e.g. 2026-05-20).")


def prompt_keep_time(label, current_cs):
    """
    Ask for a new time in MM:SS.cc format, showing the current one in brackets.
    Returns the time in centiseconds, or the current value if the user presses Enter.
    """
    display = db.cs_to_time(current_cs)
    while True:
        value = input(f"{label} (MM:SS.cc) [{display}]: ").strip()
        if not value:  # the user has pressed Enter
            return current_cs
        try:
            return db.time_to_cs(value)
        except ValueError as e:  # time entered by the user is not in the right format
            print(f"  {e}")


def prompt_date(label, optional=False):
    """
    Ask the user for a date in YYYY-MM-DD format.
    Returns None if optional and user pressed Enter without typing.
    """
    while True:
        if optional:
            date = input(
                f"{label} (YYYY-MM-DD, optional - press Enter to skip): "
            ).strip()
            if not date:
                return None
        else:
            date = input(f"{label} (YYYY-MM-DD): ").strip()
        if _is_valid_date(date):
            return date
        print(" Invalid date format. Please use YYYY-MM-DD (e.g. 2026-05-20).")


def prompt_year(label, optional=False):
    """
    Ask the user for a year in YYYY format.
    Returns the year as an integer.
    Returns None if optional and user pressed Enter without typing.
    """
    while True:
        if optional:
            year = input(f"{label} (YYYY, optional - press Enter to skip): ").strip()
            if not year:
                return None
        else:
            year = input(f"{label} (YYYY): ").strip()
        if year.isdigit() and len(year) == 4:
            return int(year)
        print("  Invalid year format.  Please use YYYY (e.g. 2026).")


def full_name(first_name, middle_name, last_name):
    """
    Return a swimmer's full name, omitting the middle name when there is none.
    """
    return f"{first_name} {middle_name + ' ' if middle_name else ''}{last_name}"


def confirm(question):
    """
    Ask the user a yes/no question.  True means yes and False means no.
    Anything other than y, yes, n or no is rejected and the question repeated.
    """
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter y or n.")


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
            selection = items[int(choice) - 1]
            print(f"  Selected: {label_fn(selection)}")
            return selection
        print("  Invalid choice, please try again.")


def search_from_list(items, label_fn, title, current=None):
    """
    Display a filtered list of items containing letter(s) typed by the user.  Return
    the item the user picks.  Returns None if the user cancels with 0.  Pressing Enter
    lists all items, or, if a current value is available, keeps it and returns it
    unchanged.
    """
    print(title)
    if current is not None:
        print(f"  Current: {label_fn(current)}")
        prompt = "Type letters to search, press Enter to keep, or 0 to cancel: "
    else:
        prompt = "Type letters to search, press Enter to list all, or 0 to cancel: "
    print("  0. Cancel")
    while True:
        search = input(prompt).strip().lower()
        if search == "0":
            return None  # selection cancelled
        if not search and current is not None:
            print(f"  Kept: {label_fn(current)}")
            return current
        filtered = [item for item in items if search in label_fn(item).lower()]
        if not filtered:
            print("  No items containing those letter(s). Try again.")
        elif len(filtered) == 1:
            print(f"  Selected: {label_fn(filtered[0])}")
            return filtered[0]
        elif len(filtered) <= 5:
            return select_from_list(filtered, label_fn, title)
        else:
            print(
                f"  {len(filtered)} results found. "
                "Type more letters to narrow down to 5 or less."
            )


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

    # Note to user
    print(
        "\n"
        "  Note to the user regarding RELAYS:\n"
        "  For relays, select the team's total distance (e.g. 400m for 4x100m).\n"
        "  To record a medley relay leg, select 'Medley' stroke.\n"
        "  Leg order: 1-Backstroke, 2-Breaststroke, 3-Butterfly, 4-Freestyle.\n"
    )

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
    distance = select_from_list(
        distances,
        lambda d: f"{d}m",
        "Select distance (for relays, select the team's total distance)",
    )
    if distance is None:
        return None  # selection cancelled

    # Check Individual or Relay
    ultimate = [d for d in stroke_disciplines if d["distance"] == distance]
    if len(ultimate) == 1:
        return ultimate[0]  # only one option, no need to ask
    options = ["Individual", "Relay"]
    selection = select_from_list(
        options, lambda o: o, "Is this an individual event or a relay event?"
    )
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

    # Note to user
    print(
        "\n"
        "  Note to the user regarding RELAYS:\n"
        "  For relays, select the team's total distance (e.g. 400y for 4x100y).\n"
        "  To record a medley relay leg, select 'Medley' stroke.\n"
        "  Leg order: 1-Backstroke, 2-Breaststroke, 3-Butterfly, 4-Freestyle.\n"
    )

    # Pick a stroke
    disciplines = db.list_disciplines_yards()
    strokes = sorted(set(d["stroke"] for d in disciplines))
    stroke = select_from_list(strokes, lambda s: s, "Select stroke")
    if stroke is None:
        return None  # selection cancelled

    # Pick a distance
    stroke_disciplines = [d for d in disciplines if d["stroke"] == stroke]
    distances = sorted(set(d["distance"] for d in stroke_disciplines))
    distance = select_from_list(
        distances,
        lambda d: f"{d}y",
        "Select distance (for relays, select the team's total distance)",
    )
    if distance is None:
        return None  # selection cancelled

    # Check Individual or Relay
    ultimate = [d for d in stroke_disciplines if d["distance"] == distance]
    if len(ultimate) == 1:
        return ultimate[0]  # only one option, no need to ask
    options = ["Individual", "Relay"]
    selection = select_from_list(
        options, lambda o: o, "Is this an individual event or a relay event?"
    )
    if selection is None:
        return None  # selection cancelled
    individual = [d for d in ultimate if d["is_relay"] == 0]
    relay = [d for d in ultimate if d["is_relay"] == 1]
    return individual[0] if selection == "Individual" else relay[0]


def discipline_label(row):
    """
    Return the discipline name, with leg information appended for relay legs.
    """
    label = row["discipline"]
    if row["is_relay_leg"]:
        leg = f"leg {row['leg_number']}"
        if row["is_mixed_mf"]:
            leg += ", mixed"
        label = f"{label} ({leg})"
    return label


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
    location = prompt("City / venue", optional=True)
    country = search_from_list(
        db.list_countries(), lambda c: c["name"], "Select country"
    )
    if country is None:
        print("  Cancelled. No meet added.")
        return
    country_id = country["id"]
    notes = prompt("Notes", optional=True)
    db.add_meet(
        name=name,
        date_start=date_start,
        country_id=country_id,
        date_end=date_end,
        location=location,
        notes=notes,
    )
    print(f"  Meet '{name}' successfully added!")


def flow_add_swimmer():
    """
    Function for the user to add a swimmer.
    """
    print("--- Add Swimmer ---")
    # name
    while True:
        first_name = prompt("First name")
        if first_name:
            break
        print("  First name is required.")

    middle_name = prompt("Middle name", optional=True)

    while True:
        last_name = prompt("Last name")
        if last_name:
            break
        print("  Last name is required.")

    # DOB
    date_of_birth = prompt_date("Date of birth")

    # gender
    while True:
        gender = prompt("Gender of swimmer (enter M or F)")
        if gender and gender.upper() in ("M", "F"):
            gender = gender.upper()
            break
        print("  Please enter M or F.")

    # club
    clubs = db.list_clubs()
    if not clubs:
        print("  No clubs found. You must add a club before adding a swimmer.")
        if confirm("  Would you like to add a club now?"):
            flow_add_club()
            clubs = db.list_clubs()
            if not clubs:
                print("  Cancelled. No swimmer added.")
                return  # user cancelled club addition
        else:
            print("  Cancelled. No swimmer added.")
            return
    club = search_from_list(clubs, lambda cl: cl["name"], "Select club")
    if club is None:
        print("  Cancelled. No swimmer added.")
        return
    club_id = club["id"]

    # nationality
    country = search_from_list(
        db.list_countries(), lambda c: c["name"], "Select country (nationality)"
    )
    if country is None:
        print("  Cancelled. No swimmer added.")
        return
    country_id = country["id"]

    # call
    db.add_swimmer(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        club_id=club_id,
        country_id=country_id,
    )

    # confirmation message
    display_name = full_name(first_name, middle_name, last_name)
    print(f"  Swimmer '{display_name}' successfully added!")


def flow_add_club():
    """
    Function for the user to add a club.
    """
    print("--- Add Club ---")
    while True:
        name = prompt("Name of club")
        if name:
            break
        print("  Club's name is required.")
    country = search_from_list(
        db.list_countries(), lambda c: c["name"], "Select country"
    )
    if country is None:
        print("  Cancelled. No club added.")
        return
    country_id = country["id"]
    db.add_club(name, country_id)
    print(f"  Club '{name}' successfully added!")


def flow_add_performance():
    """
    Function for the user to add a swimmer's performance.
    """
    print("--- Add Performance ---")
    swimmers = db.list_swimmers()
    if not swimmers:
        print("  No swimmers found. Add a swimmer first.")
        return
    meets = db.list_meets()
    if not meets:
        print("  No meets found. Add a meet first.")
        return
    swimmer = search_from_list(
        swimmers, lambda s: s["name"], "Select swimmer"
    )
    if swimmer is None:
        print("  Cancelled. No performance added.")
        return
    swimmer_id = swimmer["id"]
    units = ["Metres", "Yards"]
    unit = select_from_list(units, lambda u: u, "Select Metres or Yards")
    if unit is None:
        print("  Cancelled. No performance added.")
        return
    if unit == "Metres":
        discipline = select_discipline_metres()
        if discipline is None:
            print("  Cancelled. No performance added.")
            return
        discipline_metres_id = discipline["id"]
    else:
        discipline = select_discipline_yards()
        if discipline is None:
            print("  Cancelled. No performance added.")
            return
        discipline_yards_id = discipline["id"]

    # relay specific code
    is_relay_leg = 0
    leg_number = None
    is_mixed_mf = 0
    if discipline["is_relay"]:
        relay_options = ["The team's total time", "This swimmer's individual leg time"]
        relay_choice = select_from_list(
            relay_options, lambda o: o, "What are you recording?"
        )
        if relay_choice is None:
            print("  Cancelled. No performance added.")
            return  # selection cancelled
        if relay_choice == relay_options[1]:
            is_relay_leg = 1
            # ask leg number
            while True:
                leg = prompt("Leg number (1-4)")
                if leg and leg.isdigit() and 1 <= int(leg) <= 4:
                    leg_number = int(leg)
                    break
                print("  Please enter a number between 1 and 4.")
            # ask mixed gender
            is_mixed_mf = 1 if confirm("Is this a mixed gender relay?") else 0

    meet = search_from_list(
        meets, lambda m: f"{m['date_start']} - {m['name']}", "Select meet"
    )
    if meet is None:
        print("  Cancelled. No performance added.")
        return
    meet_id = meet["id"]
    print("  Type a date, or press Enter to accept the meet's start date in brackets.")
    date = prompt_keep_date("Date of performance", meet["date_start"])
    session = None
    if confirm("Add session (AM/PM)?"):
        sessions = ["AM", "PM"]
        session = select_from_list(
            sessions, lambda s: s, "Select 'AM' (morning) or 'PM' (afternoon/evening)"
        )
    while True:
        time_str = prompt(
            "Enter time in MM:SS.cc format (minutes:seconds.centiseconds), "
            "e.g. 30.05 or 1:01.56"
        )
        if time_str is None:
            print("  Time is required.")
            continue
        try:
            time_cs = db.time_to_cs(time_str)
            break
        except ValueError as e:
            print(f"  {e}")
    points = None
    while True:
        point_str = prompt("Points (as published on result sheet)", optional=True)
        if point_str is None:
            break
        if point_str.isdigit():
            points = int(point_str)
            break
        print("  Points must be a positive whole number (integer). Please try again.")
    notes = prompt("Here you can enter your notes", optional=True)
    if unit == "Metres":
        db.add_performance_metres(
            swimmer_id=swimmer_id,
            meet_id=meet_id,
            discipline_metres_id=discipline_metres_id,
            time_cs=time_cs,
            date=date,
            session=session,
            is_relay_leg=is_relay_leg,
            leg_number=leg_number,
            is_mixed_mf=is_mixed_mf,
            points=points,
            notes=notes,
        )
    else:
        db.add_performance_yards(
            swimmer_id=swimmer_id,
            meet_id=meet_id,
            discipline_yards_id=discipline_yards_id,
            time_cs=time_cs,
            date=date,
            session=session,
            is_relay_leg=is_relay_leg,
            leg_number=leg_number,
            is_mixed_mf=is_mixed_mf,
            points=points,
            notes=notes,
        )
    print(f"  Performance {time_str} successfully added!")


def flow_list_performances():
    """
    List the performances of a swimmer, with discipline and year as optional filters.
    """
    print("--- List Performances ---")
    swimmer = search_from_list(
        db.list_swimmers(), lambda s: s["name"], "Select swimmer"
    )
    if swimmer is None:
        return
    swimmer_id = swimmer["id"]
    units = ["Metres", "Yards"]
    unit = select_from_list(units, lambda u: u, "Select Metres or Yards")
    if unit is None:
        return
    discipline_metres_id = None
    discipline_yards_id = None
    if confirm("Filter by discipline?"):
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
    year = None
    if confirm("Filter by year?"):
        year = prompt_year("Year", optional=True)
    if unit == "Metres":
        results = db.list_performances_metres(swimmer_id, discipline_metres_id, year)
    else:
        results = db.list_performances_yards(swimmer_id, discipline_yards_id, year)
    if not results:
        print("  No performances found.")
        return
    rows = []
    for r in results:
        # build discipline_label in order to add leg information
        # to the display of relay results
        discipline_label = r["discipline"]
        if r["is_relay_leg"]:
            leg = f"leg {r['leg_number']}"
            if r["is_mixed_mf"]:
                leg += ", mixed"
            discipline_label = f"{discipline_label} ({leg})"
        rows.append(
            [
                r["swimmer"],
                r["meet"],
                r["date"],
                discipline_label,
                db.cs_to_time(r["time_cs"]),
                r["points"] if r["points"] is not None else "",
                r["session"] or "",
                r["notes"] or "",
            ]
        )

    headers = [
        "Swimmer",
        "Meet",
        "Date",
        "Discipline",
        "Time",
        "Points",
        "Session",
        "Notes",
    ]
    print(tabulate(rows, headers=headers, tablefmt="github", disable_numparse=[4]))


def flow_personal_bests():
    """
    List the best performances of a swimmer, with discipline and pool size (for metres
    only) as optional filters.
    """
    print("--- List Personal Bests ---")
    swimmer = search_from_list(
        db.list_swimmers(), lambda s: s["name"], "Select swimmer"
    )
    if swimmer is None:
        return
    swimmer_id = swimmer["id"]
    units = ["Metres", "Yards"]
    unit = select_from_list(units, lambda u: u, "Select Metres or Yards")
    if unit is None:
        return
    discipline_metres_id = None
    discipline_yards_id = None
    if confirm("Filter by discipline?"):
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
    if unit == "Metres":
        pool_id = discipline["pool_id"] if discipline_metres_id else None
        bests = db.get_personal_bests_metres(swimmer_id, discipline_metres_id, pool_id)
    else:
        bests = db.get_personal_bests_yards(swimmer_id, discipline_yards_id)
    if not bests:
        print("  No performances found.")
        return
    rows = []
    if unit == "Metres":
        for best in bests:
            performances = db.get_performance_by_time_metres(
                swimmer_id, best["discipline_metres_id"], best["best_cs"]
            )
            for perf in performances:
                rows.append(
                    [
                        best["discipline"],
                        db.cs_to_time(best["best_cs"]),
                        best["points"] if best["points"] is not None else "",
                        perf["date"],
                        perf["session"] or "",
                        perf["meet"],
                        perf["notes"] or "",
                    ]
                )
    else:
        for best in bests:
            performances = db.get_performance_by_time_yards(
                swimmer_id, best["discipline_yards_id"], best["best_cs"]
            )
            for perf in performances:
                rows.append(
                    [
                        best["discipline"],
                        db.cs_to_time(best["best_cs"]),
                        best["points"] if best["points"] is not None else "",
                        perf["date"],
                        perf["session"] or "",
                        perf["meet"],
                        perf["notes"] or "",
                    ]
                )
    headers = ["Discipline", "Best Time", "Points", "Date", "Session", "Meet", "Notes"]
    print(tabulate(rows, headers=headers, tablefmt="github", disable_numparse=[1]))


def flow_list_swimmers():
    """
    List all swimmers with club and nationality.
    """
    print("--- List Swimmers ---")
    swimmers = db.list_swimmers()
    if not swimmers:
        print("  No swimmers found.")
        return
    rows = [
        [s["name"], s["date_of_birth"], s["gender"], s["club"], s["nationality"]]
        for s in swimmers
    ]
    headers = ["Swimmer", "Date of birth", "Gender", "Club", "Nationality"]
    print(tabulate(rows, headers=headers, tablefmt="github"))


def flow_list_clubs():
    """
    List all clubs with name and country.
    """
    print("--- List Clubs ---")
    clubs = db.list_clubs()
    if not clubs:
        print("  No clubs found.")
        return
    rows = [[c["name"], c["country"]] for c in clubs]
    headers = ["Club", "Country"]
    print(tabulate(rows, headers=headers, tablefmt="github"))


def flow_list_meets():
    """
    List all meets with name, start date, end date, location, country and notes.
    """
    print("--- List Meets ---")
    meets = db.list_meets()
    if not meets:
        print("  No meets found.")
        return
    rows = [
        [
            m["name"],
            m["date_start"],
            m["date_end"] or "",
            m["location"] or "",
            m["country"],
            m["notes"] or "",
        ]
        for m in meets
    ]
    headers = ["Meet", "Start date", "End date", "Location", "Country", "Notes"]
    print(tabulate(rows, headers=headers, tablefmt="github"))


def flow_lists_menu():
    """
    Show the lists submenu and dispatch to the chosen listing flow.
    """
    submenu = """
--- Lists ---
  1. List swimmers
  2. List clubs
  3. List meets
  0. Back to main menu
"""
    actions = {
        "1": flow_list_swimmers,
        "2": flow_list_clubs,
        "3": flow_list_meets,
    }
    while True:
        print(submenu)
        choice = input("  Enter the number of your menu choice: ").strip()
        if choice == "0":
            return
        action = actions.get(choice)
        if action:
            action()
            return
        print("  Invalid menu choice, please try again.")


def flow_export():
    """
    Export the data of the SwimSQL database into sheets of a spreadsheet software.
    The user can choose between open document format (ods) or Microsoft Excel (xlsx).
    The sheets created are:
    - Performances Metres
    - Performances Yards
    - Personal Bests Metres
    - Personal Bests Yards
    """
    print("--- Export ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    items = ["Open Document Format (ODS)", "Microsoft Excel (XLSX)"]
    title = "Select export format (file will be saved to your home directory):"
    export_format = select_from_list(items, lambda e: e, title)
    if export_format is None:
        return  # export cancelled
    if export_format == "Open Document Format (ODS)":
        filepath = Path.home() / f"{timestamp}_swimsql_export.ods"
        export.export_ods(filepath)
    else:
        filepath = Path.home() / f"{timestamp}_swimsql_export.xlsx"
        export.export_xlsx(filepath)
    print(f"  Export saved to: {filepath}")


def flow_edit_club():
    """
    Function for the user to edit a club.
    """
    print("--- Edit Club ---")
    clubs = db.list_clubs()
    if not clubs:
        print("  No clubs found.")
        return
    club = search_from_list(clubs, lambda cl: cl["name"], "Select club")
    if club is None:  # case where the user cancelled
        print("  Cancelled. No changes made.")
        return
    print("  Press Enter to keep the current value shown in brackets.")
    name = prompt_keep("Club name", club["name"])
    countries = db.list_countries()
    current_country = next(c for c in countries if c["id"] == club["country_id"])
    country = search_from_list(
        countries, lambda c: c["name"], "Select country", current_country
    )
    if country is None:
        print("  Cancelled. No changes made.")
        return
    country_id = country["id"]
    if not confirm("Save these changes?"):
        print("  Cancelled. No changes made.")
        return
    db.update_club(club["id"], name, country_id)
    print(f"  Club '{name}' successfully updated!")


def flow_edit_swimmer():
    """
    Function for the user to edit a swimmer.
    """
    print("--- Edit Swimmer ---")
    swimmers = db.list_swimmers()
    if not swimmers:
        print("  No swimmers found.")
        return
    swimmer = search_from_list(swimmers, lambda s: s["name"], "Select swimmer")
    if swimmer is None:
        print("  Cancelled. No changes made.")
        return
    print("  Press Enter to keep the current value shown in brackets.")
    first_name = prompt_keep("First name", swimmer["first_name"])
    middle_name = prompt_keep("Middle name", swimmer["middle_name"])
    last_name = prompt_keep("Last name", swimmer["last_name"])
    date_of_birth = prompt_keep_date("Date of birth", swimmer["date_of_birth"])
    while True:
        gender = prompt_keep("Gender (M or F)", swimmer["gender"])
        if gender.upper() in ("M", "F"):
            gender = gender.upper()
            break
        print("  Please enter M or F.")
    clubs = db.list_clubs()
    current_club = next(cl for cl in clubs if cl["id"] == swimmer["club_id"])
    club = search_from_list(clubs, lambda cl: cl["name"], "Select club", current_club)
    if club is None:
        print("  Cancelled. No changes made.")
        return
    club_id = club["id"]
    countries = db.list_countries()
    current_country = next(c for c in countries if c["id"] == swimmer["country_id"])
    country = search_from_list(
        countries,
        lambda c: c["name"],
        "Select country (nationality)",
        current_country,
    )
    if country is None:
        print("  Cancelled. No changes made.")
        return
    country_id = country["id"]
    if not confirm("Save these changes?"):
        print("  Cancelled. No changes made.")
        return
    db.update_swimmer(
        swimmer["id"],
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        club_id=club_id,
        country_id=country_id,
    )
    display_name = full_name(first_name, middle_name, last_name)
    print(f"  Swimmer '{display_name}' successfully updated!")


def flow_edit_meet():
    """
    Function for the user to edit a meet.
    """
    print("--- Edit Meet ---")
    meets = db.list_meets()
    if not meets:
        print("  No meets found.")
        return
    meet = search_from_list(
        meets, lambda m: f"{m['date_start']} - {m['name']}", "Select meet"
    )
    if meet is None:
        print("  Cancelled. No changes made.")
        return
    print("  Press Enter to keep the current value shown in brackets.")
    name = prompt_keep("Name", meet["name"])
    date_start = prompt_keep_date("Start date", meet["date_start"])
    date_end = prompt_keep_date("End date", meet["date_end"])
    location = prompt_keep("City / venue", meet["location"])
    notes = prompt_keep("Notes", meet["notes"])
    countries = db.list_countries()
    current_country = next(c for c in countries if c["id"] == meet["country_id"])
    country = search_from_list(
        countries, lambda c: c["name"], "Select country", current_country
    )
    if country is None:
        print("  Cancelled. No changes made.")
        return
    country_id = country["id"]
    if not confirm("Save these changes?"):
        print("  Cancelled. No changes made.")
        return
    db.update_meet(
        meet["id"],
        name=name,
        date_start=date_start,
        country_id=country_id,
        date_end=date_end,
        location=location,
        notes=notes,
    )
    print(f"  Meet '{name}' successfully updated!")


def flow_edit_performance():
    """
    Function for the user to edit a performance.
    Swimmer and discipline are not editable: delete the performance and enter it
    again instead.
    """
    print("--- Edit Performance ---")
    swimmers = db.list_swimmers()
    if not swimmers:
        print("  No swimmers found.")
        return
    swimmer = search_from_list(swimmers, lambda s: s["name"], "Select swimmer")
    if swimmer is None:
        print("  Cancelled. No changes made.")
        return
    units = ["Metres", "Yards"]
    unit = select_from_list(units, lambda u: u, "Select Metres or Yards")
    if unit is None:
        print("  Cancelled. No changes made.")
        return
    if unit == "Metres":
        performances = db.list_performances_metres(swimmer["id"])
    else:
        performances = db.list_performances_yards(swimmer["id"])
    if not performances:
        print("  No performances found for this swimmer.")
        return
    performance = search_from_list(
        performances,
        lambda p: (
            f"{p['date']}  {discipline_label(p)}  "
            f"{db.cs_to_time(p['time_cs'])}  {p['meet']}"
        ),
        "Select performance",
    )
    if performance is None:
        print("  Cancelled. No changes made.")
        return
    print("  Press Enter to keep the current value shown in brackets.")
    print("  To change swimmer or discipline, delete and re-enter instead.")
    time_cs = prompt_keep_time("Time", performance["time_cs"])
    date = prompt_keep_date("Date", performance["date"])
    while True:
        session = prompt_keep("Session (AM or PM)", performance["session"])
        if session is None or session.upper() in ("AM", "PM"):
            session = session.upper() if session else None
            break
        print("  Please enter AM or PM.")
    while True:
        point_str = prompt_keep("Points", performance["points"])
        if point_str is None:
            points = None
            break
        if str(point_str).isdigit():
            points = int(point_str)
            break
        print("  Points must be a positive whole number (integer). Please try again.")
    notes = prompt_keep("Notes", performance["notes"])
    meets = db.list_meets()
    current_meet = next(m for m in meets if m["id"] == performance["meet_id"])
    meet = search_from_list(
        meets,
        lambda m: f"{m['date_start']} - {m['name']}",
        "Select meet",
        current_meet,
    )
    if meet is None:
        print("  Cancelled. No changes made.")
        return
    if not confirm("Save these changes?"):
        print("  Cancelled. No changes made.")
        return
    if unit == "Metres":
        db.update_performance_metres(
            performance["id"],
            meet_id=meet["id"],
            time_cs=time_cs,
            date=date,
            session=session,
            points=points,
            notes=notes,
        )
    else:
        db.update_performance_yards(
            performance["id"],
            meet_id=meet["id"],
            time_cs=time_cs,
            date=date,
            session=session,
            points=points,
            notes=notes,
        )
    print(f"  Performance {db.cs_to_time(time_cs)} successfully updated!")


def flow_edit_menu():
    """
    Show the edit submenu and dispatch to the chosen edit flow.
    """
    submenu = """
--- Edit ---
  1. Edit club
  2. Edit swimmer
  3. Edit meet
  4. Edit performance
  0. Back to main menu
"""
    actions = {
        "1": flow_edit_club,
        "2": flow_edit_swimmer,
        "3": flow_edit_meet,
        "4": flow_edit_performance,
    }
    while True:
        print(submenu)
        choice = input("  Enter the number of your menu choice: ").strip()
        if choice == "0":
            return
        action = actions.get(choice)
        if action:
            action()
            return
        print("  Invalid menu choice, please try again.")


def flow_delete_club():
    """
    Function for the user to delete a club.
    A club with members cannot be deleted.
    """
    print("--- Delete Club ---")
    clubs = db.list_clubs()
    if not clubs:
        print("  No clubs found.")
        return
    club = search_from_list(
        clubs,
        lambda cl: f"{cl['name']} ({cl['country']})",
        "Select club",
    )
    if club is None:
        print("  Cancelled. No club deleted.")
        return
    members = db.count_swimmers_for_club(club["id"])
    if members > 0:
        print(f"  Cannot delete this club: {members} swimmer(s) are members.")
        print("  Delete or reassign those swimmers first.")
        return
    if not confirm("Delete this club? This cannot be undone."):
        print("  Cancelled. No club deleted.")
        return
    try:
        db.delete_club(club["id"])
    except ValueError as e:
        print(f"  {e}")
        return
    print(f"  Club {club['name']} ({club['country']}) successfully deleted!")


def flow_delete_swimmer():
    """
    Function for the user to delete a swimmer.
    A swimmer with performances cannot be deleted.
    """
    print("--- Delete Swimmer ---")
    swimmers = db.list_swimmers()
    if not swimmers:
        print("  No swimmers found.")
        return
    swimmer = search_from_list(
        swimmers,
        lambda s: f"{s['name']} (born {s['date_of_birth']}, {s['nationality']})",
        "Select swimmer",
    )
    if swimmer is None:
        print("  Cancelled. No swimmer deleted.")
        return
    performances = db.count_performances_for_swimmer(swimmer["id"])
    if performances > 0:
        print(
            f"  Cannot delete this swimmer: {performances} performance(s) are linked."
        )
        print("  Delete those performances first.")
        return
    print(
        f"  {swimmer['name']} ({swimmer['gender']}, born "
        f"{swimmer['date_of_birth']}, {swimmer['nationality']}, "
        f"{swimmer['club']})"
    )
    if not confirm("Delete this swimmer? This cannot be undone."):
        print("  Cancelled. No swimmer deleted.")
        return
    try:
        db.delete_swimmer(swimmer["id"])
    except ValueError as e:
        print(f"  {e}")
        return
    print(f"  Swimmer {swimmer['name']} successfully deleted!")


def flow_delete_meet():
    """
    Function for the user to delete a meet.
    A meet with performances cannot be deleted.
    """
    print("--- Delete Meet ---")
    meets = db.list_meets()
    if not meets:
        print("  No meets found.")
        return
    meet = search_from_list(
        meets,
        lambda m: f"{m['date_start']} - {m['name']}",
        "Select meet",
    )
    if meet is None:
        print("  Cancelled. No meet deleted.")
        return
    performances = db.count_performances_for_meet(meet["id"])
    if performances > 0:
        print(f"  Cannot delete this meet: {performances} performance(s) are linked.")
        print("  Delete or reassign those performances first.")
        return
    if not confirm("Delete this meet? This cannot be undone."):
        print("  Cancelled. No meet deleted.")
        return
    try:
        db.delete_meet(meet["id"])
    except ValueError as e:
        print(f"  {e}")
        return
    print(f"  Meet {meet['date_start']} - {meet['name']} successfully deleted!")


def flow_delete_performance():
    """
    Function for the user to delete a performance.
    """
    print("--- Delete Performance ---")
    swimmers = db.list_swimmers()
    if not swimmers:
        print("  No swimmers found.")
        return
    swimmer = search_from_list(swimmers, lambda s: s["name"], "Select swimmer")
    if swimmer is None:
        print("  Cancelled. No performance deleted.")
        return
    units = ["Metres", "Yards"]
    unit = select_from_list(units, lambda u: u, "Select Metres or Yards")
    if unit is None:
        print("  Cancelled. No performance deleted.")
        return
    if unit == "Metres":
        performances = db.list_performances_metres(swimmer["id"])
    else:
        performances = db.list_performances_yards(swimmer["id"])
    if not performances:
        print("  No performances found for this swimmer.")
        return
    performance = search_from_list(
        performances,
        lambda p: (
            f"{p['date']}  {discipline_label(p)}  "
            f"{db.cs_to_time(p['time_cs'])}  {p['meet']}"
        ),
        "Select performance",
    )
    if performance is None:
        print("  Cancelled. No performance deleted.")
        return
    print(f"  Swimmer: {swimmer['name']}")
    if not confirm("Delete this performance? This cannot be undone."):
        print("  Cancelled. No performance deleted.")
        return
    if unit == "Metres":
        db.delete_performance_metres(performance["id"])
    else:
        db.delete_performance_yards(performance["id"])
    print(
        f"  Performance {discipline_label(performance)} "
        f"{db.cs_to_time(performance['time_cs'])} successfully deleted!"
    )


def flow_delete_menu():
    """
    Show the delete submenu and dispatch to the chosen delete flow.
    """
    submenu = """
--- Delete ---
  1. Delete club
  2. Delete swimmer
  3. Delete meet
  4. Delete performance
  0. Back to main menu
"""
    actions = {
        "1": flow_delete_club,
        "2": flow_delete_swimmer,
        "3": flow_delete_meet,
        "4": flow_delete_performance,
    }
    while True:
        print(submenu)
        choice = input("  Enter the number of your menu choice: ").strip()
        if choice == "0":
            return
        action = actions.get(choice)
        if action:
            action()
            return
        print("  Invalid menu choice, please try again.")
