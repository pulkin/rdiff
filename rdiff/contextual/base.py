from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from ..chunk import Diff


@dataclass
class AnyDiff:
    name: str
    """
    An empty top-level diff type.
    
    Parameters
    ----------
    name
        A name this diff belongs to.
    """
