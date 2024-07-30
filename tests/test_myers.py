import array

import pytest

from rdiff.myers import search_graph_recursive
from rdiff.cmyers import search_graph_recursive as csearch_graph_recursive


def canonize(codes):
    n_horizontal = n_vertical = 0
    n = len(codes)
    for code_i in range(n + 1):
        if code_i != n:
            code = codes[code_i]
        else:
            code = 0
        if code == 1:
            n_horizontal += 1
        elif code == 2:
            n_vertical += 1
        elif n_horizontal + n_vertical:
            for i in range(code_i - n_horizontal - n_vertical, code_i - n_vertical):
                codes[i] = 1
            for i in range(code_i - n_vertical, code_i):
                codes[i] = 2
            n_horizontal = n_vertical = 0


def compute_cost(codes):
    return sum(i % 3 != 0 for i in codes)


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n, m", [(1, 1), (2, 2), (7, 4), (7, 7)])
def test_empty(driver, n, m):
    def complicated_graph(i: int, j: int) -> float:
        return 0

    cost, result = driver(n, m, complicated_graph)
    assert compute_cost(result) == cost
    assert cost == n + m
    canonize(result)
    assert list(result) == [1] * n + [2] * m


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_impl_quantized_1(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == 2 * j

    cost, result = driver(7, 4, complicated_graph)
    assert compute_cost(result) == cost
    assert cost == 3
    canonize(result)
    assert list(result) == [3, 0, 1, 3, 0, 1, 3, 0, 1, 3, 0]


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_impl_dummy_1(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == j and i % 2

    cost, result = driver(7, 4, complicated_graph)
    assert compute_cost(result) == cost
    assert cost == 7
    canonize(result)
    assert list(result) == [1, 2, 3, 0, 1, 2, 3, 0, 1, 1, 1]


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_impl_dummy_2(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == j and i % 2

    cost, result = driver(4, 7, complicated_graph)
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

    cost, result = driver(7, 4, complicated_graph, max_cost=max_cost)
    assert compute_cost(result) == cost
    assert cost == expected_cost
    canonize(result)
    assert list(result) == expected


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_str_non_periodic(driver):
    cost, result = driver(9, 9, ("aaabbbccc", "dddbbbeee"))
    assert compute_cost(result) == cost
    assert cost == 12
    canonize(result)
    assert list(result) == [1] * 3 + [2] * 3 + [3, 0] * 3 + [1] * 3 + [2] * 3


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
def test_str_non_periodic_2(driver):
    cost, result = driver(9, 9, ("aaabbbccc", "aaadddccc"))
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

    cost, result = benchmark(driver, 3 * n, n, compare)
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.benchmark(group="unicode")
def test_benchmark_str_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = "a" * n + "c" * n + "a" * n
    short_seq = "c" * n

    cost, result = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq))
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.benchmark(group="array")
def test_benchmark_array_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = array.array('q', [0] * n + [2] * n + [0] * n)
    short_seq = array.array('q', [2] * n)

    cost, result = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq))
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512, 1024])
@pytest.mark.benchmark(group="array*")
def test_benchmark_unsupported_array_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = array.array('d', [0] * n + [2] * n + [0] * n)
    short_seq = array.array('d', [2] * n)

    cost, result = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq))
    assert compute_cost(result) == cost
    assert cost == 2 * n


@pytest.mark.parametrize("driver", [search_graph_recursive, csearch_graph_recursive])
@pytest.mark.parametrize("n", [256, 512])
@pytest.mark.benchmark(group="list")
def test_benchmark_list_long_short(driver, benchmark, n):
    benchmark.group = f"{benchmark.group}-{n}"
    long_seq = [0] * n + [2] * n + [0] * n
    short_seq = [2] * n

    cost, result = benchmark(driver, len(long_seq), len(short_seq), (long_seq, short_seq))
    assert compute_cost(result) == cost
    assert cost == 2 * n
