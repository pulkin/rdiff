from pathlib import Path

import pytest
import pandas as pd

from rdiff.presentation.base import MarkdownTableFormats

from .util import diff2text, self_extract, sync_contents

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
    sync_contents(cases / f"co2_emissions/diff.{fmt}.{out_fmt}", text, test_diff_renders)


def test_readme(test_diff_renders):
    text = diff2text(cases / "readme/a.txt", cases / "readme/b.txt")
    sync_contents(cases / "readme/diff.txt", text, test_diff_renders)


def test_git_history(tmp_path, test_diff_renders):
    self_extract("0277db1191fa0189699ecf941664bdeab292f7bb", a := tmp_path / "a")
    self_extract("4cedf58add8512ea1ed13e3c38e7faf86ba227d6", b := tmp_path / "b")
    text = diff2text(a, b)
    sync_contents(cases / "git/diff.txt", text, test_diff_renders)
