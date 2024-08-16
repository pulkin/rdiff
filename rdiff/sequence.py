from collections.abc import Sequence
from typing import Optional
from array import array
from itertools import groupby

from .chunk import Diff, Chunk
from .myers import search_graph_recursive as pymyers
from .cmyers import search_graph_recursive as cmyers


_kernels = {
    None: cmyers,
    "c": cmyers,
    "py": pymyers,
}


def diff(
        a: Sequence,
        b: Sequence,
        eq=None,
        accept: float = 0.75,
        min_ratio: float = 0.75,
        max_cost: Optional[int] = None,
        kernel: Optional[str] = None,
        rtn_diff: bool = True,
        dig=None,
) -> Diff:
    """
    Computes a diff between sequences.

    Parameters
    ----------
    a
        The first sequence.
    b
        The second sequence.
    eq
        Equality measure. Can be either of these:
        - a function ``fun(i, j) -> float`` telling the similarity ratio
          from 0 (dissimilar) to 1 (equal).
        - a pair of sequences ``(a_, b_)`` substituting the input sequences
          when computing the diff. The returned chunks, however, are still
          composed of elements from a and b.
    accept
        The lower threshold for the equaity measure.
    min_ratio
        The ratio below which the algorithm exits. The values closer to 1
        typically result in faster run times while setting to 0 will force
        the algorithm to crack through even completely dissimilar sequences.
    max_cost
        The maximal cost of the diff: the number corresponds to the maximal
        count of dissimilar/misaligned elements in both sequences. Setting
        this to zero is equivalent to setting min_ratio to 1. The algorithm
        worst-case time complexity scales with this number.
    kernel
        The kernel to use:
        - 'py': python implementation of Myers diff algorithm
        - 'c': cython implementation of Myers diff algorithm
    rtn_diff
        If True, computes and returns the diff. Otherwise, returns the
        similarity ratio only. Computing the similarity ratio only is
        typically faster and consumes less memory.
    dig
        If set to ``fun(i, j) -> float``, replaces ``Chunk.eq`` in the
        returned diff with nested diffs computed by the function.

    Returns
    -------
    A ``tuple(ratio, diffs)`` with a similarity ratio and an optional list
    of aligned chunks.
    """
    n = len(a)
    m = len(b)
    if eq is None:
        eq = (a, b)
    if isinstance(eq, tuple):
        _a, _b = eq
        assert len(_a) == n
        assert len(_b) == m
    if rtn_diff:
        codes = array('b', b'\xFF' * (n + m))
    else:
        codes = None

    _kernel = _kernels[kernel]

    total_len = n + m
    if total_len == 0:
        return Diff(ratio=1, diffs=[])

    _max_cost = int(total_len * (1 - min_ratio))
    if max_cost is not None:
        _max_cost = min(_max_cost, max_cost)

    cost = _kernel(
        n=n,
        m=m,
        similarity_ratio_getter=eq,
        accept=accept,
        max_cost=_max_cost,
        out=codes,
    )
    ratio = (total_len - cost) / total_len
    if rtn_diff:
        canonize(codes)
        return Diff(
            ratio=ratio,
            diffs=list(codes_to_chunks(a, b, codes, dig=dig)),
        )
    else:
        return Diff(ratio=ratio, diffs=None)


def canonize(codes: Sequence[int]):
    """
    Canonize the codes sequence in-place.

    Parameters
    ----------
    codes
        A sequence of diff codes.
    """
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


def codes_to_chunks(a: Sequence, b: Sequence, codes: Sequence[int], dig=None) -> list[Chunk]:
    """
    Given the original sequences and diff codes, produces diff chunks.

    Parameters
    ----------
    a
    b
        The original sequences.
    codes
        Diff codes.
    dig
        A function to re-compute per-element diff for equal chunks.

    Returns
    -------
    A list of diff chunks.
    """
    i = j = 0
    for neq, group in groupby((
        code
        for code in codes
        if code != 0),
        key=lambda x: bool(x % 3),
    ):
        group = list(group)
        n = i + sum(i % 2 for i in group)
        m = j + sum(i // 2 for i in group)
        yield Chunk(
            data_a=a[i:n],
            data_b=b[j:m],
            eq=(
                False
                if neq else
                [dig(_i, _j) for _i, _j in zip(range(i, n), range(j, m))]
                if dig is not None
                else True
            ),
        )
        i = n
        j = m
