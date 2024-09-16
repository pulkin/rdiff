from collections.abc import Sequence
from typing import Optional, Union
from array import array
from itertools import groupby

from .chunk import Diff, Chunk
from .myers import search_graph_recursive as pymyers, MAX_COST
from .cmyers import search_graph_recursive as cmyers


_kernels = {
    None: cmyers,
    "c": cmyers,
    "py": pymyers,
}


def diff(
        a: Sequence[object],
        b: Sequence[object],
        eq=None,
        accept: float = 0.75,
        min_ratio: float = 0.75,
        max_cost: int = MAX_COST,
        max_delta: int = MAX_COST,
        eq_only: bool = False,
        kernel: Optional[str] = None,
        rtn_diff: bool = True,
        dig=None,
        strict: bool = True,
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
          from 0 (dissimilar) to 1 (same).
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
    max_delta
        The maximal delta of the diff. For sequences of equal lengths this number
        tells the maximal absolute difference between indeces of aligned chunks.
    eq_only
        If True, attempts to guarantee the existence of an edit script
        satisfying both min_ratio and max_cost without actually finding the
        script. This provides an early stop and further savings in run times
        is some cases. Enforces rtn_diff=False.
    kernel
        The kernel to use:
        - 'py': python implementation of Myers diff algorithm
        - 'c': cython implementation of Myers diff algorithm
    rtn_diff
        If True, computes and returns the diff. Otherwise, returns the
        similarity ratio only. Computing the similarity ratio only is
        typically faster and consumes less memory.
    dig
        Once set to ``fun(i, j)``, the values of ``Chunk.eq`` in the
        output will be replaced by the values returned by the function.
    strict
        If True, ensures that the returned diff either satisfies both
        min_ratio and max_cost or otherwise has a zero ratio.

    Returns
    -------
    A ``tuple(ratio, diffs)`` with a similarity ratio and an optional list
    of aligned chunks.
    """
    if eq_only:
        rtn_diff = False
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

    max_cost = min(max_cost, int(total_len - total_len * min_ratio))

    cost = _kernel(
        n=n,
        m=m,
        similarity_ratio_getter=eq,
        accept=accept,
        max_cost=max_cost,
        eq_only=eq_only,
        min_diag=min(n, m) - max_delta,
        max_diag=max(n, m) + max_delta,
        out=codes,
    )

    if strict and cost > max_cost:
        if rtn_diff:
            return Diff(ratio=0, diffs=[Chunk(data_a=a, data_b=b, eq=False)])
        else:
            return Diff(ratio=0, diffs=None)

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

        if neq:
            eq = False
        elif dig is None:
            eq = True
        else:
            eq = [dig(_i, _j) for _i, _j in zip(range(i, n), range(j, m))]
            # this is a work-around for nested diffs
            if all(i is True for i in eq):
                eq = True
        yield Chunk(
            data_a=a[i:n],
            data_b=b[j:m],
            eq=eq,
        )
        i = n
        j = m


def diff_nested(
        a,
        b,
        eq=None,
        min_ratio: Union[float, tuple[float]] = 0.75,
        max_cost: Union[int, tuple[int]] = MAX_COST,
        eq_only: bool = False,
        kernel: Optional[str] = None,
        rtn_diff: bool = True,
        nested_containers: tuple = (list, tuple),
        _blacklist_a: set = frozenset(),
        _blacklist_b: set = frozenset(),
) -> Union[Diff, bool]:
    """
    Computes a diff between nested sequences.

    Parameters
    ----------
    a
        The first nested sequence.
    b
        The second nested sequence.
    eq
        An optional pair of sequences ``(a_, b_)`` substituting the input
        sequences when computing the diff. The returned chunks, however, are
        still composed of elements from a and b.
    min_ratio
        The ratio below which the algorithm exits. The values closer to 1
        typically result in faster run times while setting to 0 will force
        the algorithm to crack through even completely dissimilar sequences.
        This affects which sub-sequences are considered "equal".
    max_cost
        The maximal cost of the diff: the number corresponds to the maximal
        count of dissimilar/misaligned elements in both sequences. Setting
        this to zero is equivalent to setting min_ratio to 1. The algorithm
        worst-case time complexity scales with this number.
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
    nested_containers
        A collection of types that are considered to be capable of nesting.

    Returns
    -------
    A ``tuple(ratio, diffs)`` with a similarity ratio and an optional list
    of aligned chunks. For unsupported types returns a bool telling if objects
    are equal.
    """
    a_ = a
    b_ = b
    if eq is not None:
        a_, b_ = eq

    if isinstance(min_ratio, tuple):
        min_ratio_here = min_ratio[0]
        min_ratio_pass = min_ratio[1:] if len(min_ratio) > 1 else min_ratio
    else:
        min_ratio_here = min_ratio_pass = min_ratio

    if isinstance(max_cost, tuple):
        max_cost_here = max_cost[0]
        max_cost_pass = max_cost[1:] if len(max_cost) > 1 else max_cost
    else:
        max_cost_here = max_cost_pass = max_cost

    if ((container_type := type(a_)) is type(b_)):
        if container_type in nested_containers:

            if id(a_) in _blacklist_a or id(b_) in _blacklist_b:
                raise ValueError("encountered recursive nesting of inputs")
            _blacklist_a = {*_blacklist_a, id(a_)}
            _blacklist_b = {*_blacklist_b, id(b_)}

            def _eq(i: int, j: int):
                return diff_nested(
                    a=a[i],
                    b=b[j],
                    eq=(a_[i], b_[j]),
                    min_ratio=min_ratio_pass,
                    max_cost=max_cost_pass,
                    eq_only=True,
                    kernel=kernel,
                    nested_containers=nested_containers,
                    _blacklist_a=_blacklist_a,
                    _blacklist_b=_blacklist_b,
                )

            def _dig(i: int, j: int):
                return diff_nested(
                    a=a[i],
                    b=b[j],
                    eq=(a_[i], b_[j]),
                    min_ratio=min_ratio_pass,
                    max_cost=max_cost_pass,
                    eq_only=False,
                    kernel=kernel,
                    rtn_diff=rtn_diff,
                    nested_containers=nested_containers,
                    _blacklist_a=_blacklist_a,
                    _blacklist_b=_blacklist_b,
                )
        elif issubclass(container_type, Sequence):  # inputs are containers but we do not recognize them as, potentially, nested
            _eq = (a_, b_)
            _dig = None

        else:  # inputs are not containers
            return a_ == b

    else:  # inputs are not the same type
        return a_ == b_

    result = diff(
        a=a,
        b=b,
        eq=_eq,
        accept=1e-16,
        min_ratio=min_ratio_here,
        max_cost=max_cost_here,
        eq_only=eq_only,
        kernel=kernel,
        rtn_diff=rtn_diff,
        dig=_dig,
        strict=True,
    )

    # if equal exactly return True
    if result.diffs is not None and (len(result.diffs) == 0 or (len(result.diffs) == 1 and result.diffs[0].eq is True)):
        return True
    return result
