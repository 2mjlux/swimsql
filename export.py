# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at
# http://mozilla.org/MPL/2.0/.
# Copyright (c) 2026 Michael JJ Martin (https://github.com/2mjlux)


import db
from pathlib import Path
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P
from openpyxl import Workbook
from openpyxl.styles import Font


HEADERS_PERFORMANCES_METRES = [
    "Swimmer", "Pool", "Meet", "Meet Start",
    "Discipline", "Time", "Date", "Session", "Notes"
]

HEADERS_PERFORMANCES_YARDS = [
    "Swimmer", "Meet", "Meet Start",
    "Discipline", "Time", "Date", "Session", "Notes"
]

HEADERS_PERSONAL_BESTS = [
    "Swimmer", "Discipline", "Best Time", "Date"
]


def _get_export_data():
    """
    Fetch all data needed for export from db.py.
    Returns a dictionary with four keys.
    """
    return {
        "performances_metres": db.list_all_performances_metres(),
        "performances_yards":  db.list_all_performances_yards(),
        "personal_bests_metres": db.get_all_personal_bests_metres(),
        "personal_bests_yards":  db.get_all_personal_bests_yards(),
    }


def export_ods(filepath):
    """
    Export all data to ODS format.
    Four sheets: Performances Metres, Performances Yards,
    Personal Bests Metres, Personal Bests Yards.
    """
    pass


def export_xlsx(filepath):
    """
    Export all data to XLSX format.
    Four sheets: Performances Metres, Performances Yards,
    Personal Bests Metres, Personal Bests Yards.
    """
    pass
