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
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("  Invalid choice, please try again.")


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
