from io import StringIO
from subprocess import Popen, check_output
import tarfile
from tempfile import NamedTemporaryFile

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


def self_extract(commit, dst):
    root = check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    with NamedTemporaryFile("w+b") as f:
        Popen(["git", "-C", root, "archive", commit], stdout=f).communicate()
        f.flush()
        f.seek(0)
        with tarfile.open(fileobj=f) as f_tar:
            f_tar.extractall(dst)


def sync_contents(path, content, check):
    with open(path, "r" if check else "w") as f:
        if check:
            print("START")
            print(content)
            print("===")
            print(ref := f.read())
            print("END")
            assert content == ref
            # assert content == f.read()
        else:
            f.write(content)
