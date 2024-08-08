from typing import Any, Optional, NamedTuple
from collections.abc import Sequence


class Chunk(NamedTuple):
    """
    Represents a chunk of two sequences being compared:
    either equal or not equal. A sequence of such chunks
    forms a diff.

    Parameters
    ----------
    data_a
        A chunk in the first sequence.
    data_b
        A chunk in the second sequence.
    eq
        A flag indicating whether the two are considered
        equal. Note that this does not necessarily mean
        that ``data_a == data_b``: the equality may have
        a broader meaning, depending on the context of
        the comparison.
    data_sub_diff
        An optional sub-diff comparing pairs of elements
        from data_a and data_b. This field is used in
        multidimensional diffs with ``eq==True`` to
        specify how exactly pairs of elements in data_a
        and data_b are equal.
    """
    data_a: Sequence[Any]
    data_b: Sequence[Any]
    eq: bool
    data_sub_diff: Optional[Sequence["Diff"]] = None


class Diff(NamedTuple):
    """
    Represents a generic diff.

    Parameters
    ----------
    ratio
        The similarity ratio: a number between 0 and 1 telling
        the degree of the similarity in this diff. "0" typically
        means that there are no matches in this diff while "1"
        indicates a full alignment.
    diffs
        A list of diff chunks.
    """
    ratio: float
    diffs: Optional[list[Chunk]]
