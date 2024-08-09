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
        kernel: Optional[str] = None,
        rtn_diff: bool = True,
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
    kernel
        The kernel to use:
        - 'py': python implementation of Myers diff algorithm
        - 'c': cython implementation of Myers diff algorithm
    rtn_diff
        If True, computes and returns the diff. Otherwise, returns the
        similarity ratio only. Computing the similarity ratio only is
        typically faster and consumes less memory.

    Returns
    -------
    A list of diff chunks telling which sub-sequences are aligned and which
    ones are mismatching.
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

    cost = _kernel(
        n=n,
        m=m,
        similarity_ratio_getter=eq,
        accept=accept,
        max_cost=int(total_len * (1 - min_ratio)),
        out=codes,
    )
    ratio = (total_len - cost) / total_len
    if rtn_diff:
        canonize(codes)
        return Diff(
            ratio=ratio,
            diffs=list(codes_to_chunks(a, b, codes)),
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


def codes_to_chunks(a: Sequence, b: Sequence, codes: Sequence[int]) -> list[Chunk]:
    """
    Given the original sequences and diff codes, produces diff chunks.

    Parameters
    ----------
    a
    b
        The original sequences.
    codes
        Diff codes.

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
            eq=not neq,
        )
        i = n
        j = m
