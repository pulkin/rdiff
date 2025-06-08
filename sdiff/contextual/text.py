from dataclasses import dataclass, field
from collections.abc import Mapping, Sequence
from numbers import Number

from .base import AnyDiff, profile
from ..sequence import MAX_COST, MIN_RATIO, diff_nested
from ..chunk import Diff


@dataclass
class TextDiff(AnyDiff):
    data: Diff
    stats: Mapping[str, Number] = field(default_factory=dict, compare=False)
    """
    A text diff.

    Parameters
    ----------
    name
        A name this diff belongs to.
    data
        Diff data.
    stats
        Stats associated with this diff.
    """

    def is_eq(self) -> bool:
        return all(i.eq is True for i in self.data.diffs)


@profile("text comparison")
def diff(
        a: Sequence[str],
        b: Sequence[str],
        name: str,
        min_ratio: float = MIN_RATIO,
        min_ratio_row: float = MIN_RATIO,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
) -> TextDiff:
    """
    Computes a diff between two texts.

    Parameters
    ----------
    a
        The first text.
    b
        The second text.
    name
        The name associated with this comparison.
    min_ratio
        The ratio below which the algorithm exits. The values closer to 1
        typically result in faster run times while setting to 0 will force
        the algorithm to crack through even completely dissimilar sequences.
        This affects which sub-sequences are considered "equal".
    min_ratio_row
        The ratio above which two lines of text are aligned.
    max_cost
        The maximal cost of the diff: the number corresponds to the maximal
        count of dissimilar/misaligned lines in both texts. Setting
        this to zero is equivalent to setting min_ratio to 1. The algorithm
        worst-case time complexity scales with this number.
    max_cost_row
        The maximal cost below which two lines of text are aligned.

    Returns
    ------
    The text diff.
    """
    raw_diff = diff_nested(
        a=a,
        b=b,
        min_ratio=(min_ratio, min_ratio_row),
        max_cost=(max_cost, max_cost_row),
        max_depth=2,
    )
    return TextDiff(
        name=name,
        data=raw_diff,
    )
