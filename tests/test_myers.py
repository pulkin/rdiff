import array
from random import choice, randint, seed
import warnings

import pytest

from sdiff.myers import search_graph_recursive
from sdiff.cython.cmyers import search_graph_recursive as csearch_graph_recursive
from sdiff.sequence import canonize


def compute_cost(codes):
    return sum(i % 3 != 0 for i in codes)


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n, m", [(1, 1), (2, 2), (7, 4), (7, 7)])
def test_empty(driver, n, m):
    def complicated_graph(i: int, j: int) -> float:
        return 0

    result = array.array('b', b'\xFF' * (n + m))
    cost = driver(n, m, complicated_graph, result)
    assert compute_cost(result) == cost
    assert cost == n + m
    canonize(result)
    assert list(result) == [1] * n + [2] * m


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_impl_quantized_1(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == 2 * j

    result = array.array('b', b'\xFF' * 11)
    cost = driver(7, 4, complicated_graph, result)
    assert compute_cost(result) == cost
    assert cost == 3
    canonize(result)
    assert list(result) == [3, 0, 1, 3, 0, 1, 3, 0, 1, 3, 0]


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_impl_dummy_1(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == j and i % 2

    result = array.array('b', b'\xFF' * 11)
    cost = driver(7, 4, complicated_graph, result)
    assert compute_cost(result) == cost
    assert cost == 7
    canonize(result)
    assert list(result) == [1, 2, 3, 0, 1, 2, 3, 0, 1, 1, 1]


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_impl_dummy_2(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == j and i % 2

    result = array.array('b', b'\xFF' * 11)
    cost = driver(4, 7, complicated_graph, result)
    assert compute_cost(result) == cost
    assert cost == 7
    canonize(result)
    assert list(result) == [1, 2, 3, 0, 1, 2, 3, 0, 2, 2, 2]


@pytest.mark.parametrize("max_cost, expected_cost, expected", [
    (2, 7, [3, 0] + [1] * 5 + [2] * 2 + [3, 0]),
    (3, 3.0, [3, 0, 1, 3, 0, 1, 3, 0, 1, 3, 0]),  # 3 is the the breakpoint for this case
])
@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_max_cost_quantized(driver, max_cost, expected_cost, expected):
    def complicated_graph(i: int, j: int) -> float:
        return i == 2 * j

    result = array.array('b', b'\xFF' * 11)
    cost = driver(7, 4, complicated_graph, result, max_cost=max_cost)
    assert compute_cost(result) == cost
    assert cost == expected_cost
    canonize(result)
    assert list(result) == expected


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_eq_only(driver):
    result = array.array('b', b'\xFF' * 18)
    with pytest.warns(UserWarning, match="the 'out' argument is ignored for eq_only=True"):
        cost = driver(9, 9, ("aaabbbccc", "aaaxxxccc"), result, eq_only=True, max_cost=8)
    assert cost == 6


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_str_non_periodic(driver):
    result = array.array('b', b'\xFF' * 18)
    cost = driver(9, 9, ("aaabbbccc", "dddbbbeee"), result)
    assert compute_cost(result) == cost
    assert cost == 12
    canonize(result)
    assert list(result) == [1] * 3 + [2] * 3 + [3, 0] * 3 + [1] * 3 + [2] * 3


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_str_non_periodic_2(driver):
    result = array.array('b', b'\xFF' * 18)
    cost = driver(9, 9, ("aaabbbccc", "aaadddccc"), result)
    assert compute_cost(result) == cost
    assert cost == 6
    canonize(result)
    assert list(result) == [3, 0] * 3 + [1] * 3 + [2] * 3 + [3, 0] * 3


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_max_calls(driver):
    a = "_0aaa1_"
    b = "_2aaa3_"
    assert driver(len(a), len(b), (a, b)) == 4
    assert driver(len(a), len(b), (a, b), max_calls=2) == 10


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512])
@pytest.mark.parametrize("rtn_diff", [False, True])
@pytest.mark.benchmark(group="call")
def test_benchmark_call_long_short(driver, benchmark, n, rtn_diff):
    benchmark.group = f"{benchmark.group}-{n}"
    def compare(i, j):
        seed(j + (i << 16))
        return choice([0, 1])

    if rtn_diff:
        result = array.array('b', b'\xFF' * (4 * n))
    else:
        result = None
    cost = benchmark(driver, 3 * n, n, compare, result)
    if rtn_diff:
        assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.parametrize("rtn_diff", [False, True])
@pytest.mark.benchmark(group="unicode")
def test_benchmark_str_long_short(driver, benchmark, n, rtn_diff):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = ''.join(choice("ac") for _ in range(3 * n))
    short_seq = ''.join(choice("ac") for _ in range(n))

    if rtn_diff:
        result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    else:
        result = None
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    if rtn_diff:
        assert compute_cost(result) == cost


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.parametrize("rtn_diff", [False, True])
@pytest.mark.benchmark(group="array")
def test_benchmark_array_long_short(driver, benchmark, n, rtn_diff):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = array.array('q', [randint(0, 1) for _ in range(3 * n)])
    short_seq = array.array('q', [randint(0, 1) for _ in range(n)])

    if rtn_diff:
        result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    else:
        result = None
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    if rtn_diff:
        assert compute_cost(result) == cost


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512])
@pytest.mark.parametrize("rtn_diff", [False, True])
@pytest.mark.benchmark(group="list")
def test_benchmark_list_long_short(driver, benchmark, n, rtn_diff):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = [randint(0, 1) for _ in range(3 * n)]
    short_seq = [randint(0, 1) for _ in range(n)]

    if rtn_diff:
        result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    else:
        result = None
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    if rtn_diff:
        assert compute_cost(result) == cost
    assert cost == 2 * n
