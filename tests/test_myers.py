import array

import pytest

from rdiff.myers import search_graph_recursive
from rdiff.cmyers import search_graph_recursive as csearch_graph_recursive
from rdiff.sequence import canonize


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
@pytest.mark.parametrize("n", [256, 512])
@pytest.mark.benchmark(group="call")
def test_benchmark_call_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    def compare(i, j):
        return n <= i < 2 * n

    result = array.array('b', b'\xFF' * (4 * n))
    cost = benchmark(driver, 3 * n, n, compare, result)
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.benchmark(group="unicode")
def test_benchmark_str_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = "a" * n + "c" * n + "a" * n
    short_seq = "c" * n

    result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.benchmark(group="array")
def test_benchmark_array_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = array.array('q', [0] * n + [2] * n + [0] * n)
    short_seq = array.array('q', [2] * n)

    result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.benchmark(group="array*")
def test_benchmark_unsupported_array_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = array.array('d', [0] * n + [2] * n + [0] * n)
    short_seq = array.array('d', [2] * n)

    result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512])
@pytest.mark.benchmark(group="list")
def test_benchmark_list_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = [0] * n + [2] * n + [0] * n
    short_seq = [2] * n

    result = array.array('b', b'\xFF' * (len(long_seq) + len(short_seq)))
    cost = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq), result)
    assert compute_cost(result) == cost
    assert cost == 2 * n
