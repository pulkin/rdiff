from io import StringIO

import pandas as pd

from rdiff.contextual.table import diff as diff_table
from rdiff.presentation.base import TextPrinter


def csv2text(path, **kwargs):
    a = pd.read_csv(path / "a.csv")
    b = pd.read_csv(path / "b.csv")
    diff = diff_table(a, b, "table.csv", **kwargs)

    buffer = StringIO()
    printer = TextPrinter(printer=buffer)
    printer.print_table(diff)

    return buffer.getvalue()