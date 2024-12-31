from io import StringIO

from rdiff.contextual.path import diff_path
from rdiff.presentation.base import TextPrinter


def csvdiff2text(path, printer_kwargs=None, **kwargs):
    if printer_kwargs is None:
        printer_kwargs = {}
    diff = diff_path(path / "a.csv", path / "b.csv", "table.csv", **kwargs)

    buffer = StringIO()
    printer = TextPrinter(printer=buffer, **printer_kwargs)
    printer.print_table(diff)

    return buffer.getvalue()


def textdiff2text(path, printer_kwargs=None, **kwargs):
    if printer_kwargs is None:
        printer_kwargs = {}
    diff = diff_path(path / "a.txt", path / "b.txt", "some.txt", **kwargs)

    buffer = StringIO()
    printer = TextPrinter(printer=buffer, **printer_kwargs)
    printer.print_text(diff)

    return buffer.getvalue()
