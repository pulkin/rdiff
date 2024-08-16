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
def test_sub_str_early_stop_1(kernel):
    assert diff("xxx", "a xxx xx", kernel=kernel, min_ratio=0).ratio == 6 / 11


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_sub_str_early_stop_2(kernel):
    assert diff("xxx", "a xxx xx", kernel=kernel, min_ratio=0.9) == Diff(
        ratio=4 / 11,
        diffs=[
            Chunk(data_a="x", data_b="a xxx ", eq=False),
            Chunk(data_a="xx", data_b="xx", eq=True),
        ],
    )


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_sub_str_early_stop_2(kernel):
    assert diff("xxx", "a xxx xx", kernel=kernel, max_cost=2) == Diff(
        ratio=4 / 11,
        diffs=[
            Chunk(data_a="x", data_b="a xxx ", eq=False),
            Chunk(data_a="xx", data_b="xx", eq=True),
        ],
    )


@pytest.mark.parametrize("kernel", ["py", "c"])
def test_equal_str_nested(kernel):
    a, b = ["alice1", "bob1", "xxx"], ["alice2", "bob2"]

    def _eq(i: int, j: int):
        return diff(a[i], b[j])

    assert diff(a, b, kernel=kernel, eq=_eq, dig=_eq) == Diff(
        ratio=0.8,
        diffs=[
            Chunk(data_a=["alice1", "bob1"], data_b=["alice2", "bob2"], eq=[
                Diff(ratio=5 / 6, diffs=[
                    Chunk(data_a="alice", data_b="alice", eq=True),
                    Chunk(data_a="1", data_b="2", eq=False),
                ]),
                Diff(ratio=3 / 4, diffs=[
                    Chunk(data_a="bob", data_b="bob", eq=True),
                    Chunk(data_a="1", data_b="2", eq=False),
                ]),
            ]),
            Chunk(data_a=["xxx"], data_b=[], eq=False),
        ],
    )
