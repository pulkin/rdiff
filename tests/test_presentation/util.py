from io import StringIO

import pandas as pd

from rdiff.contextual.table import diff as diff_table
from rdiff.contextual.text import diff as diff_text
from rdiff.presentation.base import TextPrinter


def csvdiff2text(path, printer_kwargs=None, **kwargs):
    if printer_kwargs is None:
        printer_kwargs = {}
    a = pd.read_csv(path / "a.csv")
    b = pd.read_csv(path / "b.csv")
    diff = diff_table(a, b, "table.csv", **kwargs)

    buffer = StringIO()
    printer = TextPrinter(printer=buffer, **printer_kwargs)
    printer.print_table(diff)

    return buffer.getvalue()


def textdiff2text(path, printer_kwargs=None, **kwargs):
    if printer_kwargs is None:
        printer_kwargs = {}
    with open(path / "a.txt") as fa, open(path / "b.txt") as fb:
        diff = diff_text(list(fa), list(fb), "some.txt", **kwargs)

    buffer = StringIO()
    printer = TextPrinter(printer=buffer, **printer_kwargs)
    printer.print_text(diff)

    return buffer.getvalue()
