from pathlib import Path

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


def test_readme(test_diff_renders):
    text = diff2text(cases / "readme/a.txt", cases / "readme/b.txt")
    if test_diff_renders:
        with open(cases / "readme/diff.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "readme/diff.txt", "w") as f:
            f.write(text)
