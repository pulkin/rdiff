from pathlib import Path

import pytest
import pandas as pd

from rdiff.presentation.base import MarkdownTableFormats

from .util import diff2text

cases = Path(__file__).parent / "cases"


@pytest.mark.parametrize("fmt, p_kwargs, ext", [
    ("csv", {}, "txt"),
    ("feather", {}, "txt"),
    ("parquet", {}, "txt"),
    ("csv", {"table_formats": MarkdownTableFormats()}, "md"),
])
def test_co2(tmp_path, test_diff_renders, fmt, p_kwargs, ext):
    if fmt == "csv":
        base = cases / "co2_emissions"
    else:
        for n in "ab":
            getattr(pd.read_csv(cases / f"co2_emissions/{n}.csv"), f"to_{fmt}")(tmp_path / f"{n}.{fmt}")
        base = tmp_path

    text = diff2text(base / f"a.{fmt}", base / f"b.{fmt}", min_ratio=0, min_ratio_row=0, printer_kwargs=p_kwargs)

    with open(cases / f"co2_emissions/diff.{fmt}.{ext}", "r" if test_diff_renders else "w") as f:
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
