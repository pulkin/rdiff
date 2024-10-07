from typing import Optional, Union

import numpy as np

from .chunk import Diff
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
        max_depth: int = MAX_COST,
) -> Diff:
    """
    Computes a diff between nested sequences.

    Parameters
    ----------
    a
        The first array.
    b
        The second array.
    eq
        An optional pair of arrays ``(a_, b_)`` substituting the input
        arrays when computing the diff. The returned chunks, however, are
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
    max_depth
        Maximal recursion depth while exploring a and b.

    Returns
    -------
    A diff object describing the diff.
    """
    a = np.ascontiguousarray(a)
    b = np.ascontiguousarray(b)
    assert a.ndim == b.ndim

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
