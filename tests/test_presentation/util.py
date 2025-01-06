from io import StringIO

from rdiff.cli.processor import process_iter
from rdiff.presentation.base import TextPrinter


def diff2text(a, b, printer_kwargs=None, **kwargs):
    if printer_kwargs is None:
        printer_kwargs = {}

    buffer = StringIO()
    printer = TextPrinter(printer=buffer, **printer_kwargs)
    for i in process_iter(a, b, **kwargs):
        printer.print_diff(i)

    return buffer.getvalue()
