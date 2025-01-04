from dataclasses import dataclass, field
from sys import stdout
from io import TextIOBase
import os
from typing import Union, Any, Optional
from collections.abc import Sequence, Callable, Iterator
from itertools import groupby

from ..contextual.base import AnyDiff
from ..contextual.table import TableDiff
from ..contextual.text import TextDiff
from ..contextual.path import PathDiff
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


class TableBreak(str):
    pass


class TableHline(str):
    pass


@dataclass
class Table:
    column_mask: Sequence[bool]
    data: list[Union[tuple[str, ...], str]] = field(default_factory=list)
    etc: str = "..."
    pre_str: Callable[(Any,), str] = str
    """
    Represents a simple table.
    
    Parameters
    ----------
    column_mask
        Columns to display. The total number of columns
        is the length of this mask.
    data
        Column / cell data.
    etc
        A constant string to replace blocks of columns that
        are not displayed.
    pre_str
        A function pre-converting objects to str.
    """

    @property
    def row_len(self) -> int:
        """
        The number of rows displayed, including placeholders
        for rows that are skipped.
        """
        return sum(
            sum(1 for _ in group)
            if key
            else 1
            for key, group in groupby(self.column_mask)
        )

    def append_break(self, s: str):
        """
        Appends a break string.

        Parameters
        ----------
        s
            The break string.
        """
        self.data.append(TableBreak(s))

    def append_hline(self, s: str):
        """
        Appends a horizontal line.

        Parameters
        ----------
        s
            A printing symbol or sequence of symbols
            composing the line.
        """
        self.data.append(TableHline(s))

    def append_row(self, row: Sequence[object]):
        """
        Appends a table row. Additional elements in the
        row will be skipped.

        Parameters
        ----------
        row
            A sequence of objects to add as a row.
        """
        row_repr = []
        row_iter = iter(row)
        for key, group in groupby(self.column_mask):
            if key:
                for _ in group:
                    row_repr.append(self.pre_str(next(row_iter)))
            else:
                for _ in group:
                    next(row_iter)
                row_repr.append(self.etc)
        self.data.append(tuple(row_repr))

    def get_full_widths(self) -> list[int]:
        """
        Computes actual row widths.

        Returns
        -------
        A list of integers with row widths.
        """
        return [max(len(d[i]) for d in self.data if type(d) is tuple) for i in range(self.row_len)]

    def compute(self, join: str, widths: Optional[list[int]] = None) -> Iterator[str]:
        """
        Computes the table.

        Parameters
        ----------
        join
            A string for joining cells.
        widths
            Row widths to use. Defaults to ``self.get_full_widths()``.

        Returns
        -------
        A sequence of table rows.
        """
        if widths is None:
            widths = self.get_full_widths()

        for i in self.data:
            if isinstance(i, tuple):
                yield join.join(align(s, n) for s, n in zip(i, widths))
            elif isinstance(i, TableBreak):
                yield str(i)
            elif isinstance(i, TableHline):
                yield join.join((i * (w // len(i) + 1))[:w] for w in widths)
            else:
                raise ValueError(f"unknown row type: {type(i)}")


@dataclass(kw_only=True)
class TextFormats:
    skip_equal: str = "(%d lines match)"
    line_ctx: str = "  %s"
    line_add: str = "> %s"
    line_rm: str = "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = "---\n"
    chunk_add: str = "+++%s+++"
    chunk_rm: str = "---%s---"


@dataclass(kw_only=True)
class TableFormats:
    skip_equal: str = "(%d rows match)"
    column_plain: str = "%s"
    column_add: str = "+%s"
    column_rm: str = "-%s"
    column_both: str = "%s>%s"
    ix_row_plain: str = "%d"
    ix_row_add: str = "%d+"
    ix_row_rm: str = "%d-"
    ix_row_both: str = "%d>%d"
    ix_row_a: str = "%dA"
    ix_row_b: str = "%dB"
    row_head: str = ""
    row_spacer: str = " "
    row_tail: str = ""
    hline: str = "-"


@dataclass(kw_only=True)
class MarkdownTableFormats(TableFormats):
    row_head: str = "| "
    row_spacer: str = " | "
    row_tail: str = " |"


@dataclass
class TextPrinter:
    printer: TextIOBase = stdout
    context_size: int = 2
    verbosity: int = 0
    table_collapse_columns: bool = False
    width : int = 0
    table_formats: TableFormats = field(default_factory=TableFormats)
    text_formats: TextFormats = field(default_factory=TextFormats)
    """
    A simple diff printer.
    
    Parameters
    ----------
    printer
        The text printer.
    context_size
        The number of non-diff rows to surround diffs with.
    verbosity
        The verbosity level.
    table_collapse_columns
        If True, collapses table columns that do not contain diffs.
    width
        Total table width.
    table_formats
        Table formats.
    """
    def __post_init__(self):
        if not self.width:
            try:
                self.width = os.get_terminal_size(self.printer.fileno()).columns
            except (AttributeError, ValueError, OSError):
                self.width = 80

    def print_diff(self, diff: AnyDiff):
        """
        Prints diff.

        Parameters
        ----------
        diff
            A diff to process.
        """
        if isinstance(diff, TextDiff):
            self.print_text(diff)
        elif isinstance(diff, TableDiff):
            self.print_table(diff)
        elif isinstance(diff, PathDiff):
            self.print_path(diff)
        else:
            raise NotImplementedError(f"unknown diff: {diff}")

    def print_header(self, diff: AnyDiff):
        """
        Prints diff header.

        Parameters
        ----------
        diff
            A diff to process.
        """
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

    def print_path(self, diff: PathDiff):
        """
        Print a path diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        p = self.printer.write
        p(f"{diff.name} are not equal")
        if self.verbosity >= 1 and diff.message is not None:
            p(f" ({diff.message})")
        p("\n")

    def print_text(self, diff: TextDiff):
        """
        Prints a text diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        self.print_header(diff)
        formats = {
            (True, False, False): self.text_formats.line_rm,
            (False, True, False): self.text_formats.line_add,
            (True, True, False): self.text_formats.line_ctx,
            (True, True, True): self.text_formats.line_aligned,
        }

        separator = False
        for is_skip, group in groupby(diff.data.iter_important(context_size=self.context_size), lambda i: isinstance(i, int)):
            if is_skip:
                for i in group:
                    self.printer.write(self.text_formats.skip_equal % (i,) + "\n")
                    separator = False
            else:
                for key, group_2 in groupby(group, lambda i: (i.a is not None, i.b is not None, i.diff is not None)):
                    if separator:
                        self.printer.write(self.text_formats.block_spacer)
                    separator = True
                    fmt = formats[key]
                    for i in group_2:
                        if i.a is None:  # addition
                            self.printer.write(fmt % (i.b,))

                        elif i.b is None:  # removal
                            self.printer.write(fmt % (i.a,))

                        elif i.diff is None:  # context
                            self.printer.write(fmt % (i.a,))

                        else:  # inline diff
                            assert i.diff is not None
                            line = "".join(
                                c.data_a
                                if c.eq
                                else
                                "".join(
                                    _fmt % (_i,)
                                    for _fmt, _i in [
                                        (self.text_formats.chunk_rm, c.data_a),
                                        (self.text_formats.chunk_add, c.data_b),
                                    ]
                                    if _i
                                )
                                for c in i.diff.diffs
                            )
                            self.printer.write(fmt % (line,))


    def print_table(self, diff: TableDiff):
        """
        Prints a table diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        self.print_header(diff)

        # hide columns (optionally)
        if self.table_collapse_columns:
            show_col = [True, *~diff.data.eq.all(axis=0)]
        else:
            show_col = [True] * (diff.data.eq.shape[1] + 1)
        table = Table(column_mask=show_col)

        # print column names
        if diff.columns is not None:
            row = [""]
            for col_a, col_b in zip(diff.columns.a, diff.columns.b):
                if col_a == col_b:
                    col = self.table_formats.column_plain % (col_a,)
                elif not col_a:
                    col = self.table_formats.column_add % (col_b,)
                elif not col_b:
                    col = self.table_formats.column_rm % (col_a,)
                else:
                    col = self.table_formats.column_both % (col_a, col_b)
                row.append(col)
            table.append_row(row)

        table.append_hline(self.table_formats.hline)

        # print table data
        for i in diff.data.to_plain().iter_important(context_size=self.context_size):
            if isinstance(i, int):
                table.append_break(self.table_formats.skip_equal % (i,))
            elif isinstance(i, Item):

                if i.a is None:  # addition
                    table.append_row([self.table_formats.ix_row_add % (i.ix_b,), *i.b])

                elif i.b is None:  # removal
                    table.append_row([self.table_formats.ix_row_rm % (i.ix_a,), *i.a])

                elif i.diff is None:  # context
                    if i.ix_a == i.ix_b:
                        code = self.table_formats.ix_row_plain % (i.ix_a,)
                    else:
                        code = self.table_formats.ix_row_both % (i.ix_a, i.ix_b)
                    table.append_row([code, *i.a])

                else:  # inline diff
                    table.append_row([self.table_formats.ix_row_a % (i.ix_a,), *i.a])
                    table.append_row([self.table_formats.ix_row_b % (i.ix_b,), *i.b])

        for row in table.compute(self.table_formats.row_spacer):
            self.printer.write(self.table_formats.row_head + row + self.table_formats.row_tail + "\n")