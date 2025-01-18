from pathlib import Path

import pytest
import pandas as pd

from .util import diff2text, git_self_extract, sync_contents

cases = Path(__file__).parent / "cases"


@pytest.mark.parametrize("fmt, out_fmt", [
    ("csv", "plain"),
    ("feather", "plain"),
    ("parquet", "plain"),
    ("excel", "plain"),
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
    text = diff2text(base / f"a.{fmt}", base / f"b.{fmt}", min_ratio=0, min_ratio_row=0, output_format=out_fmt)
    sync_contents(cases / f"co2_emissions/diff.{fmt}.{out_fmt}", text, test_diff_renders)


def test_readme(test_diff_renders):
    text = diff2text(cases / "readme/a.txt", cases / "readme/b.txt")
    sync_contents(cases / "readme/diff.txt", text, test_diff_renders)


@pytest.mark.parametrize("args, name", [
    ({}, "default"),
    ({"output_format": "summary"}, "summary")
])
def test_git_history(tmp_path, test_diff_renders, args, name):
    git_self_extract("0c197f2cdb0bf8c0ca95e76a837296fbebad436d", a := tmp_path / "a")
    git_self_extract("e807d333433209f9328decc8290d40c270d832cd", b := tmp_path / "b")
    text = diff2text(a, b, **args)
    sync_contents(cases / f"git/diff-{name}.txt", text, test_diff_renders)
