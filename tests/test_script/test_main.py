from pathlib import Path

import pytest

from .util import git_self_extract, process2text, sync_contents

cases = Path(__file__).parent / "cases"


@pytest.mark.parametrize("args, name", [
    ([], "default.txt"),
    (["--format", "color"], "color.txt"),
    (["--format", "md"], "markdown.md"),
    (["--format", "summary"], "summary.txt"),
    (["--exclude", "tests/", "--format", "summary"], "exclude-1.txt"),
    (["--exclude", "tests/test_presentation/cases/co2_emissions/", "--format", "summary"], "exclude-2.txt"),
    (["--reverse", "--format", "summary"], "reverse.txt"),
])
def test_git(tmp_path, test_diff_renders, args, name):
    git_self_extract("0c197f2cdb0bf8c0ca95e76a837296fbebad436d", a := tmp_path / "a")
    git_self_extract("e807d333433209f9328decc8290d40c270d832cd", b := tmp_path / "b")
    code, text = process2text([str(a), str(b), *args])
    sync_contents(cases / f"git/diff-{name}", text, test_diff_renders)
    assert code is True


@pytest.mark.parametrize("args, name", [
    ([], "default.txt"),
    (["--format", "color"], "color.txt"),
    (["--format", "md"], "markdown.md"),
    (["--format", "summary"], "summary.txt"),
])
def test_readme(test_diff_renders, args, name):
    code, text = process2text([str(cases / "readme/a.txt"), str(cases / "readme/b.txt"), *args])
    sync_contents(cases / f"readme/diff-{name}", text, test_diff_renders)
    assert code is True


@pytest.mark.parametrize("b", ["single-edit", "rm-row", "add-row", "add-col", "rm-col"])
@pytest.mark.parametrize("args, name", [
    ([], "default.txt"),
    (["--format", "color"], "color.txt"),
    (["--format", "md"], "markdown.md"),
    (["--format", "summary"], "summary.txt"),
])
def test_co2_emissions(test_diff_renders, b, args, name):
    code, text = process2text([
        str(cases / "co2_emissions/a.csv"), str(cases / f"co2_emissions/b-{b}.csv"), "--min-ratio-row", "0.8", *args
    ])
    sync_contents(cases / f"co2_emissions/diff-{b}-{name}", text, test_diff_renders)
    assert code is True


@pytest.mark.parametrize("b", ["rename-col"])
@pytest.mark.parametrize("args, name", [
    ([], "default.txt"),
    (["--align-col-data"], "precise.txt"),
    (["--align-col-data", "--format", "color"], "precise-color.txt"),
    (["--align-col-data", "--format", "md"], "precise-markdown.md"),
    (["--align-col-data", "--format", "summary"], "precise-summary.txt"),
])
def test_co2_emissions_2(test_diff_renders, b, args, name):
    code, text = process2text([
        str(cases / "co2_emissions/a.csv"), str(cases / f"co2_emissions/b-{b}.csv"), *args
    ])
    sync_contents(cases / f"co2_emissions/diff-{b}-{name}", text, test_diff_renders)
    assert code is True
