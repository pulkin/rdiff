"""
A Myers diff algorithm, adapted from http://blog.robertelder.org/diff-algorithm/
"""
import warnings
from array import array
from typing import Callable
from itertools import groupby


MAX_COST = 0xFFFFFFFF  # a reasonably high maximal diff cost
MAX_CALLS = 0xFFFFFFFF  # maximal calls
MAX_DEPTH = 0xFF  # maximal recursion depth
MIN_RATIO = 0.749  # minimal similarity ratio


def search_graph_recursive(
        n: int,
        m: int,
        similarity_ratio_getter: Callable[[int, int], float],
        out: array = None,
        accept: float = 1,
        max_cost: int = MAX_COST,
        max_calls: int = MAX_CALLS,
        eq_only: bool = False,
        max_depth: int = MAX_DEPTH,
        no_python: bool = False,
        i: int = 0,
        j: int = 0,
) -> int:
    """
    Myers algorithm: Looks for the shortest path from
    (0, 0) to (n, m) in a graph representing edit
    scripts turning a sequence of size n into a
    sequence of size m.

    This is a recursive implementation which starts
    from both ends of the graph meeting somewhere in the
    middle. It then uses the middle point to split the
    problem into two smaller ones. This allows finding
    the optimal script using a linear amount of memory.

    Parameters
    ----------
    n
        The length of the first sequence.
    m
        The length of the second sequence.
    similarity_ratio_getter
        A callable(i, j) telling the similarity ratio between
        element i of the first sequence and element j
        of the second sequence.
    out
        The buffer to write the edit script to. If None (default)
        will skip writing the edit script and compute the diff
        cost only. The edit script as an array of these integers:

        - 1 for horizontal moves ("deletions")
        - 2 for vertical moves ("additions")
        - 3 followed by zero for diagonal moves ("same").
    accept
        The minimal similarity ratio to accept as "equal".
    max_cost
        The maximal allowed cost of the graph path
        (edit script). This has the meaning of the
        maximal number of additions and deletions allowed
        in the final diff. Setting this to smaller values
        allows earlier returns.
    max_calls
        The maximal number of calls (iterations) after which
        the algorithm gives up. This has to be lower than n * m
        to have any effect.
    eq_only
        If True, only figures out whether there is an edit script
        with the cost equal or below max_cost without further
        optimizing it. When this argument set to True, nothing
        is writen to `out`.

        Note that without specifying max_cost explicitly
        setting eq_only=True will return almost instantly as
        the default value of max_cost is very large.
    max_depth
        Maximal recursion depth.
    no_python
        If True will disallow slow python-based comparison protocols
        (c kernel only).
    i, j
        Offsets for calling similarity_ratio_getter and
        writing the edit script.

    Returns
    -------
    The diff cost: the number of deletions + the number
    of additions.
    """
    if no_python:
        raise ValueError("cannot set no_python in py kernel")
    if eq_only and out is not None:
        warnings.warn("the 'out' argument is ignored for eq_only=True")

    if isinstance(similarity_ratio_getter, tuple):
        _a, _b = similarity_ratio_getter

        def similarity_ratio_getter(_i: int, _j: int) -> float:
            return _a[_i] == _b[_j]

    n_calls = 2  # takes into account additional calls in the two loops below
    max_cost = min(max_cost, n + m)

    # strip the sequence from matching ends
    # this optimizes the most common case (matching beginning and end of sequence)
    # and exits the recursion for cost = 0, 1
    # this ensures that recursion calls are performed with non-zero cost
    # preventing the possibility of an infinite recursion

    # forward
    while n * m > 0 and similarity_ratio_getter(i, j) >= accept:
        n_calls += 1
        ix = i + j
        if out is not None:
            out[ix] = 3
            out[ix + 1] = 0
        i += 1
        j += 1
        n -= 1
        m -= 1

    # ... and reverse
    while n * m > 0 and similarity_ratio_getter(i + n - 1, j + m - 1) >= accept:
        n_calls += 1
        ix = i + j + n + m - 2
        if out is not None:
            out[ix] = 3
            out[ix + 1] = 0
        n -= 1
        m -= 1

    if n * m == 0:
        if out is not None:
            for ix in range(i + j, i + j + n):
                out[ix] = 1
            for ix in range(i + j + n, i + j + n + m):
                out[ix] = 2
        return n + m

    if max_depth == 0:
        # write "special" codes indicating WIP
        if out is not None:
            for ix in range(i + j, i + j + n):
                out[ix] = 5
            for ix in range(i + j + n, i + j + n + m):
                out[ix] = 6
        return n + m

    """
    adapted from http://blog.robertelder.org/diff-algorithm/
    
    First, the diff problem is presented as a directed graph problem
    where nodes are sitting on an n x m grid. Each node is connected
    to adjacent grid points, some nodes are connected along the diagonal.
    The aim is to find the shortest "edit script": a path connecting
    (0, 0) and (n, m).
    
      0   1   2   3   4
    0 ◉︎ → ◉︎ → ◉︎ → ◉︎ → ◉︎
      ↓ ↘ ↓   ↓   ↓   ↓
    1 ◉︎ → ◉︎ → ◉︎ → ◉︎ → ◉︎
      ↓   ↓   ↓ ↘ ↓ ↘ ↓
    2 ◉︎ → ◉︎ → ◉︎ → ◉︎ → ◉︎
      ↓   ↓ ↘ ↓   ↓   ↓
    3 ◉︎ → ◉︎ → ◉︎ → ◉︎ → ◉︎
    
    (n=4, m=3 in the above example)
    
    The cost of the edit script is an integer indicating how many
    horizontal and vertical edges it contains.
    Thus, the edit script with a minimal cost would include the
    maximal possible number of diagonal moves that come for free.
    In the present implementation, diagonal edges are defined implicitly:
    the digaonal move ``(i, j) -> (i + 1, j + 1)`` is present if
    (and only if) ``diag(i, j) >= accept``.
    
    A generic breadth-first search will work here but it requires ``O(n * m)``
    memory to remember the cost of reaching each of the nodes on the grid.
    Thus, the second trick is to track the progress of the breadth-first
    search along diagonals only which has a lower O(min(n, m)) memory
    requirement. The drawback is that we will not be able to recover
    the optimal path in the end of the search. But we will still be able
    to compute its cost.
    
    To visualise the approach, you may rotate the graph by 45d.
    
                 0    0                     progress
        ----------- ◉ ---------------     < 0
        |    1    ↙   ↘   1         |
        |       ◉   ↓   ◉           |     < 1
        |2    ↙   ↘   ↙   ↘   2     |
        |   ◉       ◉       ◉       |     < 2
     3  | ↙   ↘   ↙   ↘   ↙   ↘   3 |
        ◉       ◉       ◉       ◉   |     < 3
        | ↘   ↙   ↘   ↙   ↘   ↙   ↘ | 4
        |   ◉   ↓   ◉   ↓   ◉       ◉     < 4
        |     ↘   ↙   ↘   ↙   ↘   ↙ |
        |       ◉       ◉   ↓   ◉   |     < 5
        |         ↘   ↙   ↘   ↙     |
        |           ◉       ◉       |     < 6
        |             ↘   ↙         |
        --------------- ◉ -----------     < 7
    
        ^   ^   ^   ^   ^   ^   ^   ^
        0   1   2   3   4   5   6   7       diagonal
    
    Effectively, 0<=x<=n and 0<=y<=m coordinates are transformed into
    "diagonal" and "progress" coordinates: both running 0..n + m.
    At each iteration if the breadth-first search we update the
    "front": that is, for each diagonal value we increase the "progress"
    by 1 or more if we are allowed to move along the former diagonals.
    
    The third trick is to perform two updates simultaneously: downwards
    from (0, 0) and upwards from (n, m). When the two fronts meet
    (somewhere in the middle) we stop and recover one point of the
    optimal edit script. Then, we may perform recursive calls to recover
    the rest of the edit script.
    """
    nm = min(n, m) + 1
    n_m = n + m
    front_forward = array('Q', (0,) * nm)
    # the progress of the reverse front starts at n + m
    front_reverse = array('Q', (n_m,) * nm)
    fronts = (front_forward, front_reverse)
    dimensions = (n, m)

    # we, effectively, iterate over the cost itself
    # though it may also be seen as a round counter
    for cost in range(max_cost + 1):
        # early return for eq_only

        # first, figure out whether step is reverse or not
        is_reverse_front = cost % 2
        reverse_as_sign = 1 - 2 * is_reverse_front  # +- 1 depending on the direction

        # one of the fronts is updated, another one we "face"
        front_updated = fronts[is_reverse_front]

        # figure out the range of diagonals we are dealing with
        # turn 0 (even): [n]
        # turn 1 (odd) : [m]
        # turn 2 (even): [n - 1:n + 1]
        # turn 3 (odd) : [m - 1:m + 1]
        # ...
        # (even turns)
        # turn 2 * n    : [0:?]
        # turn 2 * n + 2: [1:?]
        # ...

        # source and destination diagonals from the point of view of
        # the front being updated
        diag_src = dimensions[1 - is_reverse_front]
        diag_dst = dimensions[is_reverse_front]

        # the range of diagonals here
        _p = cost // 2
        diag_updated_from = abs(diag_src - _p)
        diag_updated_to = n_m - abs(diag_dst - _p)
        # the range of diagonals facing
        # (to check for return)
        _p = (cost - 1) // 2 + 1
        diag_facing_from = abs(diag_dst - _p)
        diag_facing_to = n_m - abs(diag_src - _p)

        # phase 1: propagate diagonals
        # every second diagonal is propagated during each iteration
        for diag in range(diag_updated_from, diag_updated_to + 2, 2):
            # we simply use modulo size for indexing
            # you can also keep diag_from to always correspond to the 0th
            # element of the front or any other alignment but having
            # modulo is just the simplest
            ix = (diag // 2) % nm

            # remember the progress coordinates: starting, current
            progress = progress_start = front_updated[ix]

            # now, turn (diag, progress) coordinates into (x, y)
            # progress = x + y
            # diag = x - y + m
            # since the (x, y) -> (x + 1, y + 1) diag is polled through similarity_ratio_getter(x, y)
            # we need to shift the (x, y) coordinates when reverse
            x = (progress + diag - m) // 2 - is_reverse_front
            y = (progress - diag + m) // 2 - is_reverse_front

            # slide down the progress coordinate
            while 0 <= x < n and 0 <= y < m:
                n_calls += 1
                if similarity_ratio_getter(x + i, y + j) < accept:
                    break
                progress += 2 * reverse_as_sign
                x += reverse_as_sign
                y += reverse_as_sign
            front_updated[ix] = progress

            # if front and reverse overlap we are done
            # to figure this out we first check whether we are facing ANY diagonal
            if diag_facing_from <= diag <= diag_facing_to and (diag - diag_facing_from) % 2 == 0:
                # second, we are checking the progress
                if front_forward[ix] >= front_reverse[ix]:  # check if the two fronts (start) overlap
                    if out is not None:
                        # write the diagonal
                        for ix in range(progress_start - 2 * is_reverse_front, progress - 2 * is_reverse_front, 2 * reverse_as_sign):
                            out[i + j + ix] = 3
                            out[i + j + ix + 1] = 0

                        # recursive calls
                        x = (progress_start + diag - m) // 2
                        y = (progress_start - diag + m) // 2
                        x2 = (progress + diag - m) // 2
                        y2 = (progress - diag + m) // 2
                        if is_reverse_front:
                            # swap these two around
                            x, y, x2, y2 = x2, y2, x, y

                        search_graph_recursive(
                            n=x,
                            m=y,
                            similarity_ratio_getter=similarity_ratio_getter,
                            out=out,
                            accept=accept,
                            max_cost=cost // 2 + cost % 2,
                            max_depth=max_depth - 1,
                            i=i,
                            j=j,
                        )
                        search_graph_recursive(
                            n=n - x2,
                            m=m - y2,
                            similarity_ratio_getter=similarity_ratio_getter,
                            out=out,
                            accept=accept,
                            max_cost=cost // 2,
                            max_depth=max_depth - 1,
                            i=i + x2,
                            j=j + y2,
                        )
                    return cost

        if n_calls > max_calls:
            break

        # phase 2: make "horizontal" and "vertical" steps into adjacent diagonals
        #
        # to avoid additional memory usage we need to dance around the order and some
        # other details of how the update is performed
        # each diagonal is updated based on the value of two adjacent diagonals
        # from the point of view of the ``front_updated`` array, there are 4 possible update patterns,
        # depending on whether diagonals are even or odd, whether update is forward or reverse
        # and whether n > m or not
        #
        # (1) fw: even -> odd n > m
        #     bw: even -> odd n < m
        #      0   2   4   6
        #    [ ◉   ◉   ◉   ◉ ]
        #      ↓ ↙ ↓ ↙ ↓ ↙ ↓
        #    [ ◉   ◉   ◉   ◉ ]
        #      1   3   5   7
        #
        # (2) fw: odd -> even n < m
        #     bw: odd -> even n > m
        #      1   3   5   7
        #    [ ◉   ◉   ◉   ◉ ]
        #      ↓ ↘ ↓ ↘ ↓ ↘ ↓
        #    [ ◉   ◉   ◉   ◉ ]
        #      0   2   4   6
        #
        # (3) fw: odd -> even n > m
        #     bw: odd -> even n < m
        #      1   3   5   7   9
        #    [ ◉   ◉   ◉   ◉ | ○ ]
        #        ↘ ↓ ↘ ↓ ↘ ↓ ↘
        #    [ ◉   ◉   ◉   ◉ | ○ ]
        #     (8)  2   4   6   8
        #
        # (4) fw: even -> odd n < m
        #     bw: even -> odd n > m
        #     (8)  2   4   6   8
        #    [ ◉   ◉   ◉   ◉ | ○ ]
        #        ↙ ↓ ↙ ↓ ↙ ↓ ↙
        #    [ ◉   ◉   ◉   ◉ | ○ ]
        #      1   3   5   7
        #

        cost_2_ = cost // 2 + 1
        diag_updated_from_ = abs(diag_src - cost_2_)
        diag_updated_to_ = n_m - abs(diag_dst - cost_2_)

        ix = -1
        previous = -1

        for diag_ in range(diag_updated_from_, diag_updated_to_ + 2, 2):

            # source and destination indexes for the update
            progress_left = front_updated[((diag_ - 1) // 2) % nm]
            progress_right = front_updated[((diag_ + 1) // 2) % nm]

            if diag_ == diag_updated_from - 1:  # possible in cases 2, 4
                progress = progress_right
            elif diag_ == diag_updated_to + 1:  # possible in cases 1, 3
                progress = progress_left
            elif is_reverse_front:
                progress = min(progress_left, progress_right)
            else:
                progress = max(progress_left, progress_right)

            # the idea here is to delay updating the front by one iteration
            # such that the new progress values do not interfer with the original ones
            if ix != -1:
                front_updated[ix] = previous + reverse_as_sign

            previous = progress
            ix = (diag_ // 2) % nm

        front_updated[ix] = previous + reverse_as_sign

    if out is not None:
        for ix in range(i + j, i + j + n):
            out[ix] = 1
        for ix in range(i + j + n, i + j + n + m):
            out[ix] = 2
    return n + m


def resume_search(
        similarity_ratio_getter: Callable[[int, int], float],
        out: array,
        kernel=search_graph_recursive,
        accept: float = 1,
        max_depth: int = MAX_DEPTH,
        no_python: bool = False,
) -> int:
    """
    Resumes the previous recursive search.

    Parameters
    ----------
    similarity_ratio_getter
    out
    kernel
    accept
    max_depth
    no_python
        See `search_graph_recursive` for the description.

    Returns
    -------
    The diff cost: the number of deletions + the number
    of additions.
    """
    x = y = 0
    iterator = groupby(out)
    cost = 0
    for key, chunk in iterator:
        n = len(list(chunk))
        if key == 1:
            cost += n
            x += n
        elif key == 2:
            cost += n
            y += n
        elif key == 3:
            x += n
            y += n
        elif key == 5:
            key, chunk = next(iterator)
            assert key == 6
            m = len(list(chunk))
            cost += kernel(
                n=n,
                m=m,
                similarity_ratio_getter=similarity_ratio_getter,
                out=out,
                accept=accept,
                max_depth=max_depth,
                no_python=no_python,
                i=x,
                j=y,
            )
    return cost