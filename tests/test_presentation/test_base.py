from pathlib import Path
from subprocess import Popen, check_output
import tarfile

import pytest
import pandas as pd

from rdiff.presentation.base import MarkdownTableFormats

from .util import diff2text

cases = Path(__file__).parent / "cases"


@pytest.mark.parametrize("fmt, out_fmt", [
    ("csv", "txt"),
    ("feather", "txt"),
    ("parquet", "txt"),
    ("excel", "txt"),
    ("csv", "md"),
])
def test_co2(tmp_path, test_diff_renders, fmt, out_fmt):
    if fmt == "csv":
        base = cases / "co2_emissions"
    else:
        kwargs = {}
        if fmt == "excel":
            kwargs["index"] = False
        if fmt == "hdf":
            kwargs["key"] = "data"
        for n in "ab":
            getattr(pd.read_csv(cases / f"co2_emissions/{n}.csv"), f"to_{fmt}")(tmp_path / f"{n}.{fmt}", **kwargs)
        base = tmp_path
    p_kwargs = {}
    if out_fmt == "md":
        p_kwargs["table_formats"] = MarkdownTableFormats()
    text = diff2text(base / f"a.{fmt}", base / f"b.{fmt}", min_ratio=0, min_ratio_row=0, printer_kwargs=p_kwargs)

    with open(cases / f"co2_emissions/diff.{fmt}.{out_fmt}", "r" if test_diff_renders else "w") as f:
        if test_diff_renders:
            assert text == f.read()
        else:
            f.write(text)


def test_readme(test_diff_renders):
    text = diff2text(cases / "readme/a.txt", cases / "readme/b.txt")
    if test_diff_renders:
        with open(cases / "readme/diff.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "readme/diff.txt", "w") as f:
            f.write(text)


def test_git_history(tmp_path, test_diff_renders):
    a = tmp_path / "a"
    b = tmp_path / "b"
    root = check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    for src, dst in [
        ("0277db1191fa0189699ecf941664bdeab292f7bb", a),
        ("4cedf58add8512ea1ed13e3c38e7faf86ba227d6", b),
    ]:
        t = dst.parent / f"{dst.name}.tar"
        with open(t, "w+b") as f:
            Popen(["git", "-C", root, "archive", src], stdout=f).communicate()
            f.flush()
            f.seek(0)
            with tarfile.open(fileobj=f) as f_tar:
                f_tar.extractall(dst)

    text = diff2text(a, b)
    if test_diff_renders:
        with open(cases / "git/diff.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "git/diff.txt", "w") as f:
            f.write(text)
