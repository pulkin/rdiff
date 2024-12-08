from pathlib import Path

from .util import csv2text

cases = Path(__file__).parent / "cases"


def test_co2(test_diff_renders):
    text = csv2text(cases / "co2_emissions", min_ratio=0, min_ratio_row=0)
    if test_diff_renders:
        with open(cases / "co2_emissions/diff.txt", "r") as f:
            assert text == f.read()
    else:
        with open(cases / "co2_emissions/diff.txt", "w") as f:
            f.write(text)
