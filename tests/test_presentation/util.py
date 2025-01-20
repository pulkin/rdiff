from io import StringIO
from subprocess import Popen, check_output
import tarfile
from tempfile import NamedTemporaryFile

from rdiff.cli.processor import process_print
from rdiff.cli.processor import run


def diff2text(a, b, **kwargs):
    buffer = StringIO()
    process_print(a, b, output_file=buffer, sort=True, **kwargs)
    return buffer.getvalue()


def process2text(args):
    with NamedTemporaryFile("w+") as f:
        exit_code = run(args + ["--output", f.name, "--sort"])
        f.seek(0)
        return exit_code, f.read()


def git_self_extract(commit, dst):
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
            assert content == f.read()
        else:
            f.write(content)
