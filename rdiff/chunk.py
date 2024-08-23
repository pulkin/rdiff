from typing import Any, NamedTuple, Optional, Union
from collections.abc import Sequence
from functools import reduce
from operator import add


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
        equal or a list of diffs specifying in which way
        pairs of items from data_a and data_b are different.
    """
    data_a: Sequence[Any]
    data_b: Sequence[Any]
    eq: Union[bool, Sequence["Diff"]]


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

    def __float__(self):
        return float(self.ratio)

    def __le__(self, other):
        return float(self) <= other

    def __lt__(self, other):
        return float(self) < other

    def __ge__(self, other):
        return float(self) >= other

    def __gt__(self, other):
        return float(self) > other

    def get_a(self):
        """
        Computes the first sequence.

        Returns
        -------
        The first sequence.
        """
        assert self.diffs is not None
        return reduce(add, (i.data_a for i in self.diffs))

    def get_b(self):
        """
        Computes the second sequence.

        Returns
        -------
        The second sequence.
        """
        assert self.diffs is not None
        return reduce(add, (i.data_b for i in self.diffs))
