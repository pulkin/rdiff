import pytest

from rdiff.sequence import diff
from rdiff.chunk import Diff, Chunk


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_empty(kernel):
    assert diff("", "", kernel=kernel) == Diff(
        ratio=1,
        diffs=[],
    )


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_equal_str(kernel):
    s = "alice bob"
    assert diff(s, s, kernel=kernel) == Diff(
        ratio=1,
        diffs=[
            Chunk(data_a=s, data_b=s, eq=True)
        ],
    )


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_sub_str(kernel):
    assert diff("ice", "alice bob", kernel=kernel, min_ratio=0) == Diff(
        ratio=.5,
        diffs=[
            Chunk(data_a="", data_b="al", eq=False),
            Chunk(data_a="ice", data_b="ice", eq=True),
            Chunk(data_a="", data_b=" bob", eq=False),
        ],
    )


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_sub_str_early_stop(kernel):
    assert diff("rob", "alice bob", kernel=kernel) == Diff(
        ratio=1 / 3,
        diffs=[
            Chunk(data_a="r", data_b="alice b", eq=False),
            Chunk(data_a="ob", data_b="ob", eq=True),
        ],
    )
