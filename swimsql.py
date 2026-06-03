# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# http://mozilla.org/MPL/2.0/.
# Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)

import sys
import os
import db
import cli

WELCOME = """
Welcome to SwimSQL v1.0.0!

SwimSQL is a free and open-source tool for athletes and parents to build their own
database of competition swimming performances.

You own your database, which is saved on your computer at: ~/.swimsql/swimsql.db

If you wish, you can export your data to a spreadsheet (LibreOffice, Collabora,
OpenOffice, or Microsoft Excel).

SwimSQL is menu-driven and easy to use:
- Type the number of your menu choice
- Respond to prompts with your keyboard
- No mouse required

Note: v1.0.0 does not yet support editing or deleting entries. If you make an erroneous
entry, leave it and add a correct one. Editing features are planned for v1.1.0.

Happy swimming!

Michael
developer-swimmer-parent


Licensed under the Mozilla Public License 2.0
Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)
"""

MENU = """
=== SwimSQL v.1.0.0 ===
  1. Add club
  2. Add swimmer
  3. Add meet
  4. Add performance
  5. List performances
  6. Personal bests
  7. Export
  0. Quit
"""


def main():
    os.system("clear")
    db.init_db()
    print(WELCOME)
    input("  Press Enter to continue...")
    os.system("clear")  # clear again before showing menu

    actions = {
        "1": cli.flow_add_club,
        "2": cli.flow_add_swimmer,
        "3": cli.flow_add_meet,
        "4": cli.flow_add_performance,
        "5": cli.flow_list_performances,
        "6": cli.flow_personal_bests,
        "7": cli.flow_export,
    }

    while True:
        print(MENU)
        choice = input("  Enter the number of your menu choice: ").strip()
        if choice == "0":
            print("  Goodbye!")
            sys.exit(0)
        action = actions.get(choice)
        if action:
            action()
        else:
            print("  Invalid menu choice, please try again.")


if __name__ == "__main__":
    main()
