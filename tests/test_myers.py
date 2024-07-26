import pytest

from rdiff.myers import search_graph_recursive


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


@pytest.mark.parametrize("driver", [search_graph_recursive])
@pytest.mark.parametrize("n, m", [(1, 1), (2, 2), (7, 4), (7, 7)])
def test_empty(driver, n, m):
    def complicated_graph(i: int, j: int) -> float:
        return 0

    cost, result = driver(n, m, complicated_graph)
    assert compute_cost(result) == cost
    assert cost == n + m
    canonize(result)
    assert list(result) == [1] * n + [2] * m


@pytest.mark.parametrize("driver", [search_graph_recursive])
def test_impl_quantized_1(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == 2 * j

    cost, result = driver(7, 4, complicated_graph)
    assert compute_cost(result) == cost
    assert cost == 3
    canonize(result)
    assert list(result) == [3, 0, 1, 3, 0, 1, 3, 0, 1, 3, 0]


@pytest.mark.parametrize("driver", [search_graph_recursive])
def test_impl_dummy_1(driver):
    def complicated_graph(i: int, j: int) -> float:
        return i == j and i % 2

    cost, result = driver(7, 4, complicated_graph)
    assert compute_cost(result) == cost
    assert cost == 7
    canonize(result)
    assert list(result) == [1, 2, 3, 0, 1, 2, 3, 0, 1, 1, 1]


@pytest.mark.parametrize("driver", [search_graph_recursive])
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
@pytest.mark.parametrize("driver", [search_graph_recursive])
def test_max_cost_quantized(driver, max_cost, expected_cost, expected):
    def complicated_graph(i: int, j: int) -> float:
        return i == 2 * j

    cost, result = driver(7, 4, complicated_graph, max_cost=max_cost)
    assert compute_cost(result) == cost
    assert cost == expected_cost
    canonize(result)
    assert list(result) == expected
