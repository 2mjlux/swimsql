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


def export_ods(filepath):
    """Export all data to ODS format."""

def export_xlsx(filepath):
    """Export all data to XLSX format."""
