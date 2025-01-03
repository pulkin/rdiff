from io import StringIO

from rdiff.contextual.path import diff_path
from rdiff.presentation.base import TextPrinter


def diff2text(a, b, printer_kwargs=None, **kwargs):
    if printer_kwargs is None:
        printer_kwargs = {}
    diff = diff_path(a, b, f"{a.name}/{b.name}", **kwargs)

    buffer = StringIO()
    printer = TextPrinter(printer=buffer, **printer_kwargs)
    printer.print_diff(diff)

    return buffer.getvalue()
