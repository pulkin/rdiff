from pathlib import Path

import pandas as pd

from rdiff.presentation.base import MarkdownTableFormats

from .util import diff2text

cases = Path(__file__).parent / "cases"


def test_co2(test_diff_renders):
    text = diff2text(cases / "co2_emissions/a.csv", cases / "co2_emissions/b.csv", min_ratio=0, min_ratio_row=0)
    if test_diff_renders:
        with open(cases / "co2_emissions/diff.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "co2_emissions/diff.txt", "w") as f:
            f.write(text)


def test_co2_md(test_diff_renders):
    text = diff2text(cases / "co2_emissions/a.csv", cases / "co2_emissions/b.csv", min_ratio=0, min_ratio_row=0,
                     printer_kwargs={"table_formats": MarkdownTableFormats()})
    if test_diff_renders:
        with open(cases / "co2_emissions/diff.md", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "co2_emissions/diff.md", "w") as f:
            f.write(text)


def test_co2_feather(tmp_path, test_diff_renders):
    for n in "ab":
        pd.read_csv(cases / f"co2_emissions/{n}.csv").to_feather(tmp_path / f"{n}.feather")
    text = diff2text(tmp_path / "a.feather", cases / tmp_path / "b.feather", min_ratio=0, min_ratio_row=0)
    if test_diff_renders:
        with open(cases / "co2_emissions/diff.feather.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "co2_emissions/diff.feather.txt", "w") as f:
            f.write(text)


def test_co2_parquet(tmp_path, test_diff_renders):
    for n in "ab":
        pd.read_csv(cases / f"co2_emissions/{n}.csv").to_parquet(tmp_path / f"{n}.parquet")
    text = diff2text(tmp_path / "a.parquet", cases / tmp_path / "b.parquet", min_ratio=0, min_ratio_row=0)
    if test_diff_renders:
        with open(cases / "co2_emissions/diff.parquet.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "co2_emissions/diff.parquet.txt", "w") as f:
            f.write(text)


def test_readme(test_diff_renders):
    text = diff2text(cases / "readme/a.txt", cases / "readme/b.txt")
    if test_diff_renders:
        with open(cases / "readme/diff.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "readme/diff.txt", "w") as f:
            f.write(text)
