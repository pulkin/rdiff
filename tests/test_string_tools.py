from sdiff.presentation.string_tools import visible_len, align, iter_escape

import pytest


hello = "\033[30mhello\033[m"
elli = "...\033[m"


def test_iter_escape():
    assert list(iter_escape(hello)) == [("\033[30m", False), ("hello", True), ("\033[m", False)]


def test_vlen():
    assert visible_len(hello) == 5


@pytest.mark.parametrize("n", list(range(3)))
def test_align_truncate_short(n):
    with pytest.raises(ValueError, match="ellipsis is too long"):
        align(hello, n, elli=elli)


@pytest.mark.parametrize("n", list(range(4, 8)))
def test_align_truncate(n):
    result = align(hello, n, elli=elli)
    assert result == "\033[30m" + "hello"[:n - 3] + "\033[m" + elli
    assert visible_len(result) == n


@pytest.mark.parametrize("n", list(range(9, 10)))
def test_align_truncate(n):
    result = align(hello, n, elli=elli)
    assert result == hello + " " * (n - 5)
    assert visible_len(result) == n
