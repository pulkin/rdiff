from dataclasses import dataclass, field
from sys import stdout
from io import TextIOBase
import os
from typing import Union, Any, Optional
from collections.abc import Sequence, Callable, Iterator
from itertools import groupby
import re

from .string_tools import align, visible_len
from ..contextual.base import AnyDiff
from ..contextual.table import TableDiff
from ..contextual.text import TextDiff
from ..contextual.path import PathDiff, CompositeDiff, DeltaDiff
from ..chunk import Item


class TableBreak(str):
    pass


class TableHline(str):
    pass


@dataclass
class Table:
    column_mask: Sequence[bool]
    data: list[Union[tuple[str, ...], TableBreak, TableHline]] = field(default_factory=list)
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
        return [max(visible_len(d[i]) for d in self.data if type(d) is tuple) for i in range(self.row_len)]

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
    header: str = "%s"
    textwrap_start: str = ""
    textwrap_end: str = ""
    del_entry: str = "DEL %s"
    new_entry: str = "NEW %s"
    skip_equal: str = "(%d lines match)"
    line_ctx: str = "  %s"
    line_add: str = "> %s"
    line_rm: str = "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = "---\n"
    chunk_add: str = "+++%s+++"
    chunk_rm: str = "---%s---"

    @staticmethod
    def escape(s: str) -> str:
        if s.endswith("\n"):
            s, x = s[:-1], s[-1:]
        else:
            x = ""
        return repr(s)[1:-1] + x


@dataclass(kw_only=True)
class MarkdownTextFormats(TextFormats):
    header: str = "%s\n"
    textwrap_start: str = "~~~text\n"
    textwrap_end: str = "~~~\n"
    del_entry: str = "DEL %s\n"
    new_entry: str = "NEW %s\n"
    skip_equal: str = "(%d lines match)"
    line_ctx: str = "  %s"
    line_add: str = "> %s"
    line_rm: str = "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = "---\n"
    chunk_add: str = "+++%s+++"
    chunk_rm: str = "---%s---"

    @staticmethod
    def escape(s: str) -> str:
        return re.sub(f'(~~~)', r'[triple ~]', s)


_tformat = "\033[%dm%%s\033[0m"


tf_strike = _tformat % 9
tf_black = _tformat % 30
tf_red = _tformat % 31
tf_green = _tformat % 32
tf_on_red = _tformat % 41
tf_on_light_grey = _tformat % 47
tf_grey = _tformat % 90
tf_on_white = _tformat % 107


@dataclass(kw_only=True)
class TermTextFormats(TextFormats):
    header: str = (tf_on_light_grey % tf_black)[:-4]
    textwrap_start: str = ""
    textwrap_end: str = ""
    del_entry: str = f"{tf_red % 'DEL'} %s"
    new_entry: str = f"{tf_green % 'NEW'} %s"
    skip_equal: str = tf_grey % "(%d lines match)"
    line_ctx: str = tf_grey % "  %s"
    line_add: str = tf_green % "> %s"
    line_rm: str = tf_red % "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = ""
    chunk_add: str = tf_green
    chunk_rm: str = (tf_on_red % tf_black)[:-4]


@dataclass(kw_only=True)
class TableFormats:
    skip_equal: str = "(%d row(s) match)"

    column_plain: str = "%s"
    column_add: str = "+%s"
    column_rm: str = "-%s"
    column_both: str = "%s>%s"

    ix_row_context_one: str = "%d"
    ix_row_context_both: str = "%dA%dB"
    ix_row_same: str = "%d"
    ix_row_a: str = "%dA"
    ix_row_b: str = "%dB"

    data_row_context: str = "%s"
    data_row_same: str = "%s"
    data_row_a: str = "---%s---"
    data_row_b: str = "+++%s+++"

    row_head: str = ""
    row_spacer: str = " "
    row_tail: str = ""

    hline: str = "-"


@dataclass(kw_only=True)
class TermTableFormats(TableFormats):
    skip_equal: str = tf_grey % "(%d row(s) match)"

    column_plain: str = "%s"
    column_add: str = tf_green
    column_rm: str = tf_red
    column_both: str = f"{tf_red}>{tf_green}"

    ix_row_context_one: str = tf_grey % "%d"
    ix_row_context_both: str = tf_grey % "%dA%dB"
    ix_row_same: str = "%d"
    ix_row_a: str = tf_red % "%d"
    ix_row_b: str = tf_green % "%d"

    data_row_context: str = tf_grey
    data_row_same: str = "%s"
    data_row_a: str = tf_red
    data_row_b: str = tf_green

    row_head: str = ""
    row_spacer: str = " "
    row_tail: str = ""

    hline: str = ""


@dataclass(kw_only=True)
class MarkdownTableFormats(TableFormats):
    skip_equal: str = "(%d row(s) match)"

    column_plain: str = "%s"
    column_add: str = "*%s*"
    column_rm: str = "~~%s~~"
    column_both: str = "%s>%s"

    ix_row_context_one: str = "%d"
    ix_row_context_both: str = "%dA%dB"
    ix_row_same: str = "%d"
    ix_row_a: str = "~~%d~~"
    ix_row_b: str = "*%d*"

    data_row_context: str = "%s"
    data_row_same: str = "%s"
    data_row_a: str = "~~%s~~"
    data_row_b: str = "*%s*"

    row_head: str = "| "
    row_spacer: str = " | "
    row_tail: str = " |"

    hline: str = "-"


@dataclass
class AbstractTextPrinter:
    printer: TextIOBase = stdout
    verbosity: int = 0
    width: int = 0
    """
    Diff printer.

    Parameters
    ----------
    printer
        The text printer.
    verbosity
        The verbosity level.
    width
        Total screen width.
    """

    def __post_init__(self):
        if not self.width:
            try:
                self.width = os.get_terminal_size(self.printer.fileno()).columns
            except (AttributeError, ValueError, OSError):
                self.width = 80

    def print_diff(self, diff: Union[AnyDiff, Sequence[[AnyDiff]]]):
        """
        Prints diff.

        Parameters
        ----------
        diff
            A diff to process.
        """
        if diff.is_eq():
            if self.verbosity >= 2:
                self.print_equal(diff)
        elif isinstance(diff, TextDiff):
            self.print_text(diff)
        elif isinstance(diff, TableDiff):
            self.print_table(diff)
        elif isinstance(diff, PathDiff):
            self.print_path(diff)
        elif isinstance(diff, DeltaDiff):
            self.print_delta(diff)
        elif isinstance(diff, CompositeDiff):
            for _d in diff.items:
                self.print_diff(_d)
        else:
            raise NotImplementedError(f"unknown diff: {diff}")

    def print_equal(self, diff: AnyDiff):
        """
        Prints equal (empty) diff.

        Parameters
        ----------
        diff
            A diff to process.
        """
        raise NotImplementedError

    def print_path(self, diff: PathDiff):
        """
        Print a path diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        raise NotImplementedError

    def print_delta(self, diff: DeltaDiff):
        """
        Print a delta diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        raise NotImplementedError

    def print_text(self, diff: TextDiff):
        """
        Prints a text diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        raise NotImplementedError

    def print_table(self, diff: TableDiff):
        """
        Prints a table diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        raise NotImplementedError


@dataclass
class TextPrinter(AbstractTextPrinter):
    context_size: int = 2
    table_collapse_columns: bool = False
    table_formats: TableFormats = field(default_factory=TableFormats)
    text_formats: TextFormats = field(default_factory=TextFormats)
    """
    A simple diff printer.
    
    Parameters
    ----------
    printer
        The text printer.
    verbosity
        The verbosity level.
    width
        Total screen width.
    context_size
        The number of non-diff rows to surround diffs with.
    table_collapse_columns
        If True, collapses table columns that do not contain diffs.
    table_formats
        Table formats.
    text_format
        Text formats.
    """

    def print_equal(self, diff: AnyDiff):
        """
        Prints equal (empty) diff.

        Parameters
        ----------
        diff
            A diff to process.
        """
        self.printer.write(f"{diff.name} compare equal through {diff.__class__.__name__}\n")

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

        p(self.text_formats.header % f"comparing {diff.name}")
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
        if diff.eq:
            self.print_equal(diff)
        else:
            p(f"{diff.name} are not equal")
            if self.verbosity >= 1 and diff.message is not None:
                p(f" ({diff.message})")
            p("\n")

    def print_delta(self, diff: DeltaDiff):
        """
        Print a delta diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        fmt = self.text_formats.del_entry if diff.exist_a else self.text_formats.new_entry
        self.printer.write(f"{fmt % diff.name}\n")

    def print_text(self, diff: TextDiff):
        """
        Prints a text diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        self.print_header(diff)
        p = self.printer.write
        e = self.text_formats.escape
        formats = {
            (True, False, False): self.text_formats.line_rm,
            (False, True, False): self.text_formats.line_add,
            (True, True, False): self.text_formats.line_ctx,
            (True, True, True): self.text_formats.line_aligned,
        }

        separator = False
        p(self.text_formats.textwrap_start)
        for is_skip, group in groupby(diff.data.iter_important(context_size=self.context_size), lambda i: isinstance(i, int)):
            if is_skip:
                for i in group:
                    p(self.text_formats.skip_equal % (i,) + "\n")
                    separator = False
            else:
                for key, group_2 in groupby(group, lambda i: (i.a is not None, i.b is not None, i.diff is not None)):
                    if separator:
                        p(self.text_formats.block_spacer)
                    separator = True
                    fmt = formats[key]
                    for i in group_2:
                        if i.a is None and i.b is not None:  # addition
                            p(fmt % (e(i.b),))

                        elif i.b is None and i.a is not None:  # removal
                            p(fmt % (e(i.a),))

                        elif i.diff is None:  # context
                            p(fmt % (e(i.a),))

                        else:  # inline diff
                            assert i.diff is not None
                            line = "".join(
                                c.data_a
                                if c.eq
                                else
                                "".join(
                                    _fmt % (e(_i),)
                                    for _fmt, _i in [
                                        (self.text_formats.chunk_rm, c.data_a),
                                        (self.text_formats.chunk_add, c.data_b),
                                    ]
                                    if _i
                                )
                                for c in i.diff.diffs
                            )
                            p(fmt % (line,))
        p(self.text_formats.textwrap_end)

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

        if self.table_formats.hline:
            table.append_hline(self.table_formats.hline)

        # print table data
        for i in diff.data.to_plain().iter_important(context_size=self.context_size):
            if isinstance(i, int):
                table.append_break(self.table_formats.skip_equal % (i,))
            elif isinstance(i, Item):

                if i.a is None:  # addition
                    table.append_row([self.table_formats.ix_row_b % (i.ix_b,), *(self.table_formats.data_row_b % s for s in i.b)])

                elif i.b is None:  # removal
                    table.append_row([self.table_formats.ix_row_a % (i.ix_a,), *(self.table_formats.data_row_a % s for s in i.a)])

                elif i.diff is None:  # context
                    if i.ix_a == i.ix_b:
                        code = self.table_formats.ix_row_context_one % (i.ix_a,)
                    else:
                        code = self.table_formats.ix_row_context_both % (i.ix_a, i.ix_b)
                    table.append_row([code, *(self.table_formats.data_row_context % s for s in i.a)])

                else:  # inline diff
                    row_a = []
                    row_b = []
                    if i.ix_a != i.ix_b:
                        row_a.append(self.table_formats.ix_row_a % (i.ix_a,))
                        row_b.append(self.table_formats.ix_row_b % (i.ix_b,))
                    else:
                        row_a.append(self.table_formats.ix_row_same % (i.ix_a,))
                        row_b.append("")
                    for a, b, eq in zip(i.a, i.b, i.diff):
                        if eq:
                            row_a.append(self.table_formats.data_row_same % (a,))
                            row_b.append("")
                        else:
                            if a:
                                row_a.append(self.table_formats.data_row_a % (a,))
                                row_b.append(self.table_formats.data_row_b % (b,) if b else "")
                            else:
                                row_a.append(self.table_formats.data_row_b % (b,) if b else "")
                                row_b.append("")
                    table.append_row(row_a)
                    if any(row_b):
                        table.append_row(row_b)

        for row in table.compute(self.table_formats.row_spacer):
            self.printer.write(self.table_formats.row_head + row + self.table_formats.row_tail + "\n")


@dataclass(kw_only=True)
class TextSummaryFormats:
    ratio_fmt: str = "{:.4f}"
    ratio_non_fmt: str = "{:<6}"
    n_equal_fmt: str = "={:<7d}"
    n_equal_non_fmt: str = "{:<8}"
    n_neq_fmt: str = "≠{:<7d}"
    n_neq_non_fmt: str = "{:<8}"
    n_aligned_fmt: str = "≈{:<7d}"
    n_aligned_non_fmt: str = "{:<8}"
    sep = " "


@dataclass
class SummaryTextPrinter(TextPrinter):
    formats: TextSummaryFormats = field(default_factory=TextSummaryFormats)
    """
    A summary diff printer.

    Parameters
    ----------
    printer
        The text printer.
    verbosity
        The verbosity level.
    width
        Total screen width.
    formats
        Text formats.
    """

    @property
    def _empty_fmt(self) -> str:
        f = self.formats
        return f"{f.ratio_non_fmt}{f.sep}{f.n_equal_non_fmt}{f.sep}{f.n_aligned_non_fmt}{f.sep}{f.n_neq_non_fmt}{f.sep}{{}}"

    @property
    def _ratio_fmt(self) -> str:
        f = self.formats
        return f"{f.ratio_fmt}{f.sep}{f.n_equal_non_fmt}{f.sep}{f.n_aligned_non_fmt}{f.sep}{f.n_neq_non_fmt}{f.sep}{{}}"

    @property
    def _full_fmt(self) -> str:
        f = self.formats
        return f"{f.ratio_fmt}{f.sep}{f.n_equal_fmt}{f.sep}{f.n_aligned_fmt}{f.sep}{f.n_neq_fmt}{f.sep}{{}}"

    def print_equal(self, diff: AnyDiff):
        """
        Prints equal (empty) diff.

        Parameters
        ----------
        diff
            A diff to process.
        """
        self.printer.write(self._empty_fmt.format("1", "", "", "", f"{diff.name} match\n"))

    def print_path(self, diff: PathDiff):
        """
        Print a path diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        p = self.printer.write
        if diff.eq:
            self.print_equal(diff)
        else:
            p(self._empty_fmt.format("0", "", "", "", f"{diff.name} do not match\n"))
            if self.verbosity >= 1 and diff.message is not None:
                p(f" ({diff.message})")
            p("\n")

    def print_delta(self, diff: DeltaDiff):
        """
        Print a delta diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        self.printer.write(self._empty_fmt.format('DEL' if diff.exist_a else 'NEW', "", "", "", f"{diff.name}\n"))

    def print_text(self, diff: TextDiff):
        """
        Prints a text diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        if diff.data.diffs is not None:
            n_eq = sum(len(i.data_a) for i in diff.data.diffs if i.eq is True)
            n_al = sum(len(i.data_a) for i in diff.data.diffs if not isinstance(i.eq, bool))
            n_ne = sum(len(i.data_a) for i in diff.data.diffs if i.eq is False)
            self.printer.write(self._full_fmt.format(diff.data.ratio, n_eq, n_al, n_ne, f"{diff.name}\n"))
        else:
            self.printer.write(self._ratio_fmt.format(diff.data.ratio, "", "", "", f"{diff.name}\n"))

    def print_table(self, diff: TableDiff):
        """
        Prints a table diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        n_eq = diff.data.eq.all(axis=1).sum()
        n_al = diff.data.eq.any(axis=1).sum() - n_eq
        n_ne = (~diff.data.eq).all(axis=1).sum()
        self.printer.write(self._full_fmt.format(diff.data.ratio, n_eq, n_al, n_ne, f"{diff.name}\n"))
