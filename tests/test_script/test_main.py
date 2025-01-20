from pathlib import Path

from ..test_presentation.util import git_self_extract, process2text, sync_contents

cases = Path(__file__).parent / "cases"


def test_git(tmp_path, test_diff_renders):
    git_self_extract("0c197f2cdb0bf8c0ca95e76a837296fbebad436d", a := tmp_path / "a")
    git_self_extract("e807d333433209f9328decc8290d40c270d832cd", b := tmp_path / "b")
    code, text = process2text([str(a), str(b)])
    sync_contents(cases / f"diff.txt", text, test_diff_renders)
