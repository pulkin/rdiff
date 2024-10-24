from typing import Optional, Union
from collections.abc import Sequence
from collections import defaultdict
from itertools import groupby

import numpy as np

from .chunk import Diff, ChunkSignature, Signature
from .myers import MAX_COST, MAX_CALLS
from .sequence import diff_nested


def diff(
        a,
        b,
        eq=None,
        min_ratio: Union[float, tuple[float]] = 0.75,
        max_cost: Union[int, tuple[int]] = MAX_COST,
        max_delta: Union[int, tuple[int]] = MAX_COST,
        max_calls: Union[int, tuple[int]] = MAX_CALLS,
        eq_only: bool = False,
        kernel: Optional[str] = None,
        rtn_diff: bool = True,
) -> Diff:
    """
    Computes a diff between numpy tensors of equal rank.

    Parameters
    ----------
    a
        The first tensor.
    b
        The second tensor.
    eq
        An optional pair of tensors ``(a_, b_)`` substituting the input
        tensors when computing the diff. The returned chunks, however, are
        still composed of elements from a and b.
    min_ratio
        The ratio below which the algorithm exits. The values closer to 1
        typically result in faster run times while setting to 0 will force
        the algorithm to crack through even completely dissimilar sequences.
        This affects which arrays are considered "equal".
    max_cost
        The maximal cost of the diff: the number corresponds to the maximal
        count of dissimilar/misaligned elements in both sequences. Setting
        this to zero is equivalent to setting min_ratio to 1. The algorithm
        worst-case time complexity scales with this number.
    max_delta
        The maximal delta of the diff. For sequences of equal lengths this number
        tells the maximal absolute difference between indeces of aligned chunks.
    max_calls
        The maximal number of calls (iterations) after which the algorithm gives
        up. This has to be lower than ``len(a) * len(b)`` to have any effect.
    eq_only
        If True, attempts to guarantee the existence of an edit script
        satisfying both min_ratio and max_cost without actually finding the
        script. This provides an early stop is some cases and further savings
        on run times. Will enforce rtn_diff=False.
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
    A diff object describing the diff.
    """
    a = np.ascontiguousarray(a)
    b = np.ascontiguousarray(b)
    if a.ndim != b.ndim:
        raise ValueError(f"{a.ndim=} != {b.ndim=}")

    ndim = a.ndim

    return diff_nested(
        a=a,
        b=b,
        min_ratio=min_ratio,
        max_cost=max_cost,
        max_delta=max_delta,
        max_calls=max_calls,
        eq_only=eq_only,
        kernel=kernel,
        rtn_diff=rtn_diff,
        nested_containers=(np.ndarray,),
        max_depth=ndim,
    )


def common_diff_sig(n: int, m: int, diffs: Sequence[Diff]) -> Signature:
    """
    Computes a "common" diff signature using breadth-depth first.

    Parameters
    ----------
    n
    m
        Dimensions of arrays.
    diffs
        A sequence of diffs.

    Returns
    -------
    The signature as a tuple of tuples with chunk lengths and their
    equality statuses (equal/not equal).
    """
    if n == 0 or m == 0:
        return Signature(parts=[ChunkSignature(size_a=n, size_b=m, eq=False)])

    # prepare search space
    space = np.zeros((n, m), dtype=int)
    for diff in diffs:
        x = y = 0
        for chunk in diff.diffs:
            if chunk.eq:
                for i in range(len(chunk.data_a)):
                    space[x + i, y + i] += 1
            x += len(chunk.data_a)
            y += len(chunk.data_b)

    # search
    for y in range(m):
        if y == 0:
            for x in range(1, n):
                space[x, y] = max(space[x, y], space[x - 1, y])
        elif n > 0:
            space[0, y] = max(space[0, y], space[0, y - 1])
            for x in range(1, n):
                space[x, y] = max(space[x - 1, y], space[x, y - 1], space[x - 1, y - 1] + space[x, y])

    # trace back
    x = n - 1
    y = m - 1
    is_b = np.zeros(n + m, dtype=bool)
    is_eq = np.zeros(n + m + 2, dtype=bool)
    pos = n + m
    while x >= 0 and y >= 0:
        if x > 0 and space[x, y] == space[x - 1, y]:
            x -= 1
            pos -= 1
        elif y > 0 and space[x, y] == space[x, y - 1]:
            y -= 1
            pos -= 1
            is_b[pos] = 1
        else:
            is_eq[pos] = is_eq[pos - 1] = 1
            x -= 1
            y -= 1
            pos -= 2
            is_b[pos + 1] = 1
    x += 1
    y += 1
    is_b[x:x + y] = 1
    is_eq[0] = 1 - is_eq[1]
    is_eq[-1] = 1 - is_eq[-2]
    ix, = np.nonzero(is_eq[1:] != is_eq[:-1])
    return Signature(parts=tuple(
        ChunkSignature(
            size_a=int((~is_b[fr:to]).sum()),
            size_b=int((is_b[fr:to]).sum()),
            eq=bool(is_eq[fr + 1]),
        )
        for fr, to in zip(ix[:-1], ix[1:])
    ))


def get_row_col_diff(
        a: np.ndarray,
        b: np.ndarray,
        min_ratio: Union[float, tuple[float]] = 0.75,
        max_cost: Union[int, tuple[int]] = MAX_COST,
        max_delta: Union[int, tuple[int]] = MAX_COST,
        max_calls: Union[int, tuple[int]] = MAX_CALLS,
        kernel: Optional[str] = None,
) -> tuple[Signature, Signature]:
    """
    Aligns rows and columns of two matrices and returns the corresponding pair
    of diffs.

    The algorithm first computes a generic diff between the two matrices to
    determine the aligned rows. It will then use the diff withing the aligned
    rows to determine the "common" or "average" diff between the columns.

    Parameters
    ----------
    a
        The first matrix.
    b
        The second matrix.
    min_ratio
        The ratio below which the algorithm exits. The values closer to 1
        typically result in faster run times while setting to 0 will force
        the algorithm to crack through even completely dissimilar sequences.
        This affects which arrays are considered "equal".
    max_cost
        The maximal cost of the diff: the number corresponds to the maximal
        count of dissimilar/misaligned elements in both sequences. Setting
        this to zero is equivalent to setting min_ratio to 1. The algorithm
        worst-case time complexity scales with this number.
    max_delta
        The maximal delta of the diff. For sequences of equal lengths this number
        tells the maximal absolute difference between indeces of aligned chunks.
    max_calls
        The maximal number of calls (iterations) after which the algorithm gives
        up. This has to be lower than ``len(a) * len(b)`` to have any effect.
    kernel
        The kernel to use:
        - 'py': python implementation of Myers diff algorithm
        - 'c': cython implementation of Myers diff algorithm

    Returns
    -------
    Two sequences describing row and column diffs.
    """
    if a.ndim != 2:
        raise ValueError(f"{a.ndim=} is not a matrix")
    if b.ndim != 2:
        raise ValueError(f"{b.ndim=} is not a matrix")

    base_diff = diff(
        a=a,
        b=b,
        min_ratio=min_ratio,
        max_cost=max_cost,
        max_delta=max_delta,
        max_calls=max_calls,
        kernel=kernel,
    )

    row_sig = base_diff.signature
    in_row_diff = []
    for chunk in base_diff.diffs:
        if chunk.eq is not False:
            in_row_diff.extend(chunk.eq)
    col_sig = common_diff_sig(a.shape[1], b.shape[1], in_row_diff)
    return row_sig, col_sig


def align_inflate(a: np.ndarray, b: np.ndarray, val, sig: Signature, dim: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Align arrays with the given value by inflating them.

    Parameters
    ----------
    a
    b
        The arrays to align.
    val
        The scalar value to inflate with.
    sig
        The diff signature to use.
    dim
        The dimension to inflate.

    Returns
    -------
    The inflated array.
    """
    assert (ndim := a.ndim) == b.ndim

    s = sum(
        chunk.size_a + chunk.size_b * (1 - chunk.eq)
        for chunk in sig.parts
    )
    a_shape = list(a.shape)
    b_shape = list(b.shape)
    a_shape[dim] = s
    b_shape[dim] = s
    result_a = np.full(a_shape, val, dtype=a.dtype)
    result_b = np.full(b_shape, val, dtype=b.dtype)

    pre = (slice(None),) * dim
    post = (slice(None),) * (ndim - dim - 1)

    offset_a = offset_b = offset = 0
    for chunk in sig.parts:
        # a comes first
        result_a[(*pre, slice(offset, offset + chunk.size_a), *post)] = (
            a[(*pre, slice(offset_a, offset_a + chunk.size_a), *post)]
        )
        offset_a += chunk.size_a
        if not chunk.eq:
            offset += chunk.size_a
        # b is second
        result_b[(*pre, slice(offset, offset + chunk.size_b), *post)] = (
            b[(*pre, slice(offset_b, offset_b + chunk.size_b), *post)]
        )
        offset_b += chunk.size_b
        offset += chunk.size_b
    return result_a, result_b


def diff_aligned_2d(
        a,
        b,
        fill,
        eq=None,
        min_ratio: Union[float, tuple[float]] = 0.75,
        max_cost: Union[int, tuple[int]] = MAX_COST,
        max_delta: Union[int, tuple[int]] = MAX_COST,
        max_calls: Union[int, tuple[int]] = MAX_CALLS,
        kernel: Optional[str] = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes an aligned diff between numpy matrices.

    Parameters
    ----------
    a
        The first matrix.
    b
        The second matrix.
    fill
        The empty value to use when filling both matrices.
    eq
        An optional pair of tensors ``(a_, b_)`` substituting the input
        matrices when computing the diff. The returned chunks, however, are
        still composed of elements from a and b.
    min_ratio
        The ratio below which the algorithm exits. The values closer to 1
        typically result in faster run times while setting to 0 will force
        the algorithm to crack through even completely dissimilar sequences.
        This affects which arrays are considered "equal".
    max_cost
        The maximal cost of the diff: the number corresponds to the maximal
        count of dissimilar/misaligned elements in both sequences. Setting
        this to zero is equivalent to setting min_ratio to 1. The algorithm
        worst-case time complexity scales with this number.
    max_delta
        The maximal delta of the diff. For sequences of equal lengths this number
        tells the maximal absolute difference between indeces of aligned chunks.
    max_calls
        The maximal number of calls (iterations) after which the algorithm gives
        up. This has to be lower than ``len(a) * len(b)`` to have any effect.
    kernel
        The kernel to use:
        - 'py': python implementation of Myers diff algorithm
        - 'c': cython implementation of Myers diff algorithm

    Returns
    -------
    a
        Inflated matrix a.
    b
        Inflated matrix b.
    eq_matrix
        Equality matrix.
    """
    a_, b_ = a, b
    if eq is not None:
        a_, b_ = eq
    signatures = get_row_col_diff(
        a=a_,
        b=b_,
        min_ratio=min_ratio,
        max_cost=max_cost,
        max_delta=max_delta,
        max_calls=max_calls,
        kernel=kernel,
    )
    for dim, sig in enumerate(signatures):
        a, b = align_inflate(a, b, fill, sig, dim)
        if eq is not None:
            a_, b_ = align_inflate(a_, b_, fill, sig, dim)
    if eq is None:
        a_, b_ = a, b
    eq_matrix = a_ == b_
    idx = tuple()
    for dim, sig in enumerate(signatures):
        offset = 0
        for part in sig.parts:
            if not part.eq:
                eq_matrix[(*idx, slice(offset, offset + (n := part.size_a + part.size_b)))] = False
                offset += n
            else:
                offset += part.size_a
        idx = (*idx, slice(None))
    return a, b, eq_matrix
