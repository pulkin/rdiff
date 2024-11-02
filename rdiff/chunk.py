from typing import Any, Optional, Union
from collections.abc import Sequence, Iterator
from functools import reduce, cached_property
from operator import add
from itertools import chain
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkSignature:
    """
    Represents a chunk signature.

    Parameters
    ----------
    size_a
        Length of a sub-sequence in a.
    size_b
        Length of a sub-sequence in b.
    eq
        A flag indicating whether the two are considered
        equal.
    """
    size_a: int
    size_b: int
    eq: bool


@dataclass(frozen=True)
class Signature:
    """
    Represents a diff signature.

    Parameters
    ----------
    parts
        Signature constituents.
    """
    parts: Sequence[ChunkSignature]


@dataclass(frozen=True)
class Chunk:
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
    eq: Union[bool, Sequence[Union[bool, "Diff"]]]

    def to_string(self, prefix: str = "") -> str:
        eq = self.eq
        data_a = self.data_a
        data_b = self.data_b

        if eq is True:
            # plain equal
            return f"{prefix}a[]=b[]: {repr(data_a)} = {repr(data_b)}"
        elif eq is False:
            # plain not equal
            return f"{prefix}a[]≠b[]: {repr(data_a)} ≠ {repr(data_b)}"
        else:
            # a sequence of aligned elements with some differences
            result = [f"{prefix}a[]≈b[]: {repr(data_a)} ≈ {repr(data_b)}"]
            for _eq, _a, _b in zip(eq, data_a, data_b):
                if _eq is True:
                    # this was an exact comparison
                    result.append(f"{prefix}··a=b: {_a}")
                else:
                    result.append(_eq.to_string(prefix=prefix + "··"))
            return "\n".join(result)

    @cached_property
    def signature(self) -> ChunkSignature:
        return ChunkSignature(
            size_a=len(self.data_a),
            size_b=len(self.data_b),
            eq=self.eq is not False,
        )


@dataclass(frozen=True)
class Diff:
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
        if self.diffs is None:
            raise ValueError("no diff data")
        return reduce(add, (i.data_a for i in self.diffs))

    def get_b(self):
        """
        Computes the second sequence.

        Returns
        -------
        The second sequence.
        """
        if self.diffs is None:
            raise ValueError("no diff data")
        return reduce(add, (i.data_b for i in self.diffs))

    def to_string(self, prefix: str = "") -> str:
        preamble = f"{prefix}Diff({self.ratio:.4f})"
        if self.diffs is None:
            return preamble
        else:
            return "\n".join(chain((preamble + ":",), (i.to_string(prefix=prefix + "··") for i in self.diffs)))

    @cached_property
    def signature(self) -> Signature:
        if self.diffs is None:
            raise ValueError("no diff data")
        return Signature(parts=tuple(i.signature for i in self.diffs))

    def iter_important(self, context_size: int = 0) -> Iterator[Union["Item", int]]:
        """
        Iterates over non-equal item pairs.

        Parameters
        ----------
        context_size
            The number of equal pairs to provide the context
            while yielding non-equal pairs.

        Yields
        ------
        Diff items and integers specifying the number of skipped
        item pairs in-between.
        """
        def _dummy():
            return
            yield

        def _head(data_a, counter_a, data_b, counter_b):
            for (i, a), (j, b) in zip(
                enumerate(data_a[:context_size], counter_a),
                enumerate(data_b[:context_size], counter_b),
            ):
                yield Item(a=a, b=b, ix_a=i, ix_b=j)

        def _tail(data_a, counter_a, data_b, counter_b, head_size):
            gap = len(data_a) - context_size - head_size
            if gap > 0:
                yield gap
            else:
                gap = 0
            gap += head_size
            for (i, a), (j, b) in zip(
                enumerate(data_a[gap:], counter_a + gap),
                enumerate(data_b[gap:], counter_b + gap),
            ):
                yield Item(a=a, b=b, ix_a=i, ix_b=j)

        context_tail = _dummy()
        counter_a = counter_b = 0

        for i_chunk, chunk in enumerate(self.diffs):

            if chunk.eq is True:  # chunks are equal: take care of context
                if i_chunk:  # this is NOT the beginning of text: yield context
                    yield from _head(chunk.data_a, counter_a, chunk.data_b, counter_b)
                context_tail = _tail(chunk.data_a, counter_a, chunk.data_b, counter_b, bool(i_chunk) * context_size)

            elif chunk.eq is False:  # chunks are not equal: yield them all
                yield from context_tail
                for i, a in enumerate(chunk.data_a, counter_a):
                    yield Item(a=a, b=None, ix_a=i, ix_b=None)
                for j, b in enumerate(chunk.data_b, counter_b):
                    yield Item(a=None, b=b, ix_a=None, ix_b=j)

            else:  # chunks are aligned
                yield from context_tail
                for i, (a, b, diff) in enumerate(zip(chunk.data_a, chunk.data_b, chunk.eq)):
                    yield Item(a=a, b=b, ix_a=counter_a + i, ix_b=counter_b + i, diff=diff)

            counter_a += len(chunk.data_a)
            counter_b += len(chunk.data_b)

        leftover = sum(i if isinstance(i, int) else 1 for i in context_tail)
        if leftover:
            yield leftover


@dataclass(frozen=True)
class Item:
    """
    Represents a diff item.

    Parameters
    ----------
    a
    b
        The two objects in diff.
    ix_a
    ix_b
        The corresponding sequence indexes.
    diff
        An optional diff between a and b.
    """
    a: Any
    b: Any
    ix_a: Optional[int]
    ix_b: Optional[int]
    diff: Optional[Diff] = None
