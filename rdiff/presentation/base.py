from dataclasses import dataclass, field
from sys import stdout
from io import TextIOBase
import os
from typing import Union, Any
from collections.abc import Sequence, Iterable
from itertools import groupby
from operator import itemgetter

from ..contextual.base import AnyDiff
from ..contextual.table import TableDiff
from ..chunk import Item


def align(s: str, n: int, elli: str = "…", fill: str = " ", just=str.ljust) -> str:
    """
    Aligns a string towards a specific length. Truncates if the string is longer
    than the provided number and justifies it if the string is shorter.

    Parameters
    ----------
    s
        The string to align.
    n
        The desired string length.
    elli
        Suffix to add when truncating the string.
    fill
        A character to use for justifying.
    just
        Justify function.

    Returns
    -------
    The resulting string of the desired length.
    """
    if len(s) > n:
        return s[:n - len(elli)] + elli
    else:
        return just(s, n, fill)


@dataclass
class Table:
    column_mask: Sequence[bool]
    data: list[Union[tuple[str, ...], str]] = field(default_factory=list)

    @property
    def row_len(self) -> int:
        return sum(
            sum(1 for _ in group)
            if key
            else 1
            for key, group in groupby(self.column_mask)
        )

    def add_break(self, s: str):
        self.data.append(s)

    def get_etc(self, chunk: Iterable[Any]) -> str:
        return "..."

    def get_pre_str(self, o: Any) -> str:
        return str(o)

    def add_row(self, row: Sequence[object]):
        row_repr = []
        row_iter = iter(row)
        for key, group in groupby(self.column_mask):
            if key:
                for _ in group:
                    row_repr.append(self.get_pre_str(next(row_iter)))
            else:
                for _ in group:
                    next(row_iter)
                row_repr.append(self.get_etc(group))
        self.data.append(tuple(row_repr))

    def get_full_widths(self) -> list[int]:
        return [max(len(d[i]) for d in self.data if type(d) is tuple) for i in range(self.row_len)]

    def align_all(self, widths: list[int]) -> list[Union[tuple[str, ...], str]]:
        lengths = self.get_full_widths()
        return [
            tuple(align(s, n) for s, n in zip(i, lengths))
            if type(i) is tuple
            else i
            for i in self.data
        ]


@dataclass
class TextPrinter:
    printer: TextIOBase = stdout
    context_size: int = 2
    verbosity: int = 0
    table_collapse_columns: bool = False
    width : int = 0
    """
    A simple diff printer.
    """
    def __post_init__(self):
        if not self.width:
            try:
                self.width = os.get_terminal_size(self.printer.fileno()).columns
            except (AttributeError, ValueError, OSError):
                self.width = 80

    def print_header(self, diff: AnyDiff):
        p = self.printer.write
        v = self.verbosity

        p(f"comparing {diff.name}")
        if isinstance(diff, TableDiff):
            if v >= 1:
                p(f" (ratio={diff.data.ratio:.4f})")
            if v >= 2:
                p(f"\n  aligned ratio={diff.data.aligned_ratio:.4f}")
                for name, orig, inflated in [
                    ("a", diff.data.a_shape, diff.data.a.shape),
                    ("b", diff.data.b_shape, diff.data.b.shape),
                ]:
                    n = orig[0] * orig[1]
                    if n:
                        x = f"{inflated[0] * inflated[1] / n:.2f}"
                    else:
                        x = "∞"
                    p(f"\n  {name}.shape={orig} -> {inflated} x{x}")
        p("\n")

    def print_table(self, diff: TableDiff):
        self.print_header(diff)

        # hide columns (optionally)
        if self.table_collapse_columns:
            show_col = [True, *~diff.data.eq.all(axis=0)]
        else:
            show_col = [True] * (diff.data.eq.shape[1] + 1)
        table = Table(column_mask=show_col)

        # print column names
        if diff.columns is not None:
            cols_a = ["", *diff.columns.a]
            cols_b = ["", *diff.columns.b]
            if cols_a == cols_b:
                table.add_row(["", *diff.columns.a])
            else:
                table.add_row(["A", *diff.columns.a])
                table.add_row(["B", *diff.columns.b])

        # print table data
        for i in diff.data.to_plain().iter_important(context_size=self.context_size):
            if isinstance(i, int):
                table.add_break(f"({i} rows match)")
            elif isinstance(i, Item):

                if i.a is None:  # addition
                    table.add_row([f"{i.ix_b}+", *i.b])

                elif i.b is None:  # removal
                    table.add_row([f"{i.ix_a}-", *i.a])

                elif i.diff is None:  # context
                    if i.ix_a == i.ix_b:
                        code = f"{i.ix_a}"
                    else:
                        code = f"{i.ix_a}>{i.ix_b}"
                    table.add_row([code, *i.a])

                else:  # inline diff
                    table.add_row([f"{i.ix_a}A", *i.a])
                    table.add_row([f"{i.ix_a}B", *i.b])

        for row in table.align_all(table.get_full_widths()):
            self.printer.write(" ".join(row) + "\n")