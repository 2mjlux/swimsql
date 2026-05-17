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
        choice = input("Choice: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("  Invalid choice, please try again.")
