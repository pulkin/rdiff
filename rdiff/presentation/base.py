from dataclasses import dataclass, field
from sys import stdout
from io import TextIOBase
import os
from typing import Union, Any, Optional
from collections.abc import Sequence, Callable, Iterator
from itertools import groupby
import re
from html import escape as html_escape
from textwrap import dedent

from .string_tools import align, visible_len
from ..contextual.base import AnyDiff
from ..contextual.table import TableDiff
from ..contextual.text import TextDiff
from ..contextual.path import PathDiff, CompositeDiff, DeltaDiff, MIMEDiff
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
    pre_str: Callable[[Any], str] = str
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

    def get_full_widths(self, m: int = 1) -> list[int]:
        """
        Computes actual row widths.

        Parameters
        ----------
        m
            Minimal column width.

        Returns
        -------
        A list of integers with row widths.
        """
        return [max(max(visible_len(d[i]), m) for d in self.data if type(d) is tuple) for i in range(self.row_len)]

    def compute(self, join: str, widths: Optional[list[int]] = None, elli: str = "…") -> Iterator[str]:
        """
        Computes the table.

        Parameters
        ----------
        join
            A string for joining cells.
        widths
            Row widths to use.
        elli
            Ellipsis.

        Returns
        -------
        A sequence of table rows.
        """
        for i in self.data:
            if isinstance(i, tuple):
                if widths is None:
                    yield join.join(i)
                else:
                    yield join.join(align(s, n, elli=elli) for s, n in zip(i, widths))
            elif isinstance(i, TableBreak):
                yield str(i)
            elif isinstance(i, TableHline):
                if widths is None:
                    yield i
                else:
                    yield join.join((i * (w // len(i) + 1))[:w] for w in widths)
            else:
                raise ValueError(f"unknown row type: {type(i)}")


@dataclass
class TextFormats:
    header: str = "%s"
    textwrap_start: str = ""
    textwrap_end: str = ""
    del_entry: str = "DEL %s"
    new_entry: str = "NEW %s"
    mime_entry: str = "MIME %s %s ≠ %s"
    same_entry: str = "same %s"
    skip_equal: str = "(%d lines match)"
    line_ctx: str = "  %s"
    line_add: str = "> %s"
    line_rm: str = "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = "---\n"
    chunk_add: str = "+++%s+++"
    chunk_rm: str = "---%s---"

    hello: str = ""
    goodbye: str = ""

    @staticmethod
    def escape(s: str) -> str:
        if s.endswith("\n"):
            s, x = s[:-1], s[-1:]
        else:
            x = ""
        return repr(s)[1:-1] + x


@dataclass
class MarkdownTextFormats(TextFormats):
    header: str = "%s\n"
    textwrap_start: str = "~~~text\n"
    textwrap_end: str = "~~~\n"
    del_entry: str = "DEL %s\n"
    new_entry: str = "NEW %s\n"
    mime_entry: str = "MIME %s %s ≠ %s\n"
    same_entry: str = "same %s\n"
    skip_equal: str = "(%d lines match)"
    line_ctx: str = "  %s"
    line_add: str = "> %s"
    line_rm: str = "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = "---\n"
    chunk_add: str = "+++%s+++"
    chunk_rm: str = "---%s---"

    hello: str = ""
    goodbye: str = ""

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


@dataclass
class TermTextFormats(TextFormats):
    header: str = (tf_on_light_grey % tf_black)[:-4]
    textwrap_start: str = ""
    textwrap_end: str = ""
    del_entry: str = f"{tf_red % 'DEL'} %s"
    new_entry: str = f"{tf_green % 'NEW'} %s"
    mime_entry: str = "MIME %s %s ≠ %s"
    same_entry: str = "same %s"
    skip_equal: str = tf_grey % "(%d lines match)"
    line_ctx: str = tf_grey % "  %s"
    line_add: str = tf_green % "> %s"
    line_rm: str = tf_red % "< %s"
    line_aligned: str = "≈ %s"
    block_spacer: str = ""
    chunk_add: str = tf_green
    chunk_rm: str = (tf_on_red % tf_black)[:-4]

    hello: str = ""
    goodbye: str = ""


@dataclass
class HTMLTextFormats(TextFormats):
    header: str = "<h4>%s</h4>"
    textwrap_start: str = "<pre>"
    textwrap_end: str = "</pre>"
    del_entry: str = "<h4>DEL %s</h4>"
    new_entry: str = f"<h4>NEW %s</h4>"
    mime_entry: str = "<h4>MIME %s %s ≠ %s</h4>"
    same_entry: str = "<h4>same %s</h4>"
    skip_equal: str = "(%d lines match)"
    line_ctx: str = "  %s"
    line_add: str = "<span class=\"diff-add\">&gt; %s</span>"
    line_rm: str = "<span class=\"diff-rm\">&lt; %s</span>"
    line_aligned: str = "<span class=\"diff-highlight\">≈ %s</span>"
    block_spacer: str = ""
    chunk_add: str = "<span class=\"diff-add\">%s</span>"
    chunk_rm: str = "<span class=\"diff-rm\">%s</span>"

    hello: str = dedent("""
    <!DOCTYPE html><html><head>
    <meta charset=\"UTF-8\">
    <link rel="stylesheet" href="https://unpkg.com/mvp.css"> 
    <style>
      .diff-rm {
        color: #B8405E;
        text-decoration: underline;
      }
      .diff-add {
        color: #2EB086;
      }
      .diff-highlight {
        background-color: #EEE6CE;
        display: block;
      }
      .diff-context {
        color: grey;
      }
    </style>
    </head><body>\n""")
    goodbye: str = "</body></html>\n"

    @staticmethod
    def escape(s: str) -> str:
        return html_escape(s)


@dataclass
class TableFormats:
    align: bool = True

    table_head: str = ""
    table_tail: str = ""

    skip_equal: str = "(%d row(s) match)"

    column_plain: str = "%s"
    column_add: str = "+%s"
    column_rm: str = "-%s"
    column_both: str = "---%s>>>%s+++"

    ix_row_header: str = ""
    ix_row_none: str = ""
    ix_row_context_one: str = "%d"
    ix_row_context_both: str = "%dA%dB"
    ix_row_same: str = "%d"
    ix_row_a: str = "%dA"
    ix_row_b: str = "%dB"

    data_row_none: str = ""
    data_row_context: str = "%s"
    data_row_same: str = "%s"
    data_row_a: str = "---%s---"
    data_row_b: str = "+++%s+++"

    row_head: str = ""
    row_spacer: str = " "
    row_tail: str = ""

    hline: str = "-"
    elli: str = "…"


@dataclass
class TermTableFormats(TableFormats):
    align: bool = True

    table_head: str = ""
    table_tail: str = ""

    skip_equal: str = tf_grey % "(%d row(s) match)"

    column_plain: str = "%s"
    column_add: str = tf_green
    column_rm: str = tf_red
    column_both: str = f"{tf_red}{tf_green}"

    ix_row_header: str = ""
    ix_row_none: str = ""
    ix_row_context_one: str = tf_grey % "%d"
    ix_row_context_both: str = tf_grey % "%dA%dB"
    ix_row_same: str = "%d"
    ix_row_a: str = tf_red % "%d"
    ix_row_b: str = tf_green % "%d"

    data_row_none: str = ""
    data_row_context: str = tf_grey
    data_row_same: str = "%s"
    data_row_a: str = tf_red
    data_row_b: str = tf_green

    row_head: str = ""
    row_spacer: str = " "
    row_tail: str = ""

    hline: str = ""
    elli: str = "…\033[0m"


@dataclass
class MarkdownTableFormats(TableFormats):
    align: bool = True

    table_head: str = ""
    table_tail: str = ""

    skip_equal: str = "(%d row(s) match)"

    column_plain: str = "%s"
    column_add: str = "*%s*"
    column_rm: str = "~~%s~~"
    column_both: str = "~~%s~~*%s*"

    ix_row_header: str = ""
    ix_row_none: str = ""
    ix_row_context_one: str = "%d"
    ix_row_context_both: str = "%dA%dB"
    ix_row_same: str = "%d"
    ix_row_a: str = "~~%d~~"
    ix_row_b: str = "*%d*"

    data_row_none: str = ""
    data_row_context: str = "%s"
    data_row_same: str = "%s"
    data_row_a: str = "~~%s~~"
    data_row_b: str = "*%s*"

    row_head: str = "| "
    row_spacer: str = " | "
    row_tail: str = " |"

    hline: str = "-"
    elli: str = "…"


@dataclass
class HTMLTableFormats(TableFormats):
    align: bool = False

    table_head: str = "<table>"
    table_tail: str = "</table>"

    skip_equal: str = "<td colspan=\"100%%\" class=\"diff-context\">(%d row(s) match)</td>"

    column_plain: str = "<th>%s</th>"
    column_add: str = "<th class=\"diff-add\">%s</th>"
    column_rm: str = "<th class=\"diff-rm\">%s</th>"
    column_both: str = "<th><span class=\"diff-rm\">%s</span><span class=\"diff-add\">%s</span></th>"

    ix_row_header: str = "<td class=\"diff-context\">A</td><td class=\"diff-context\">B</td>"
    ix_row_none: str = "<td></td><td></td>"
    ix_row_context_one: str = "<td class=\"diff-context\">%d</td><td></td>"
    ix_row_context_both: str = "<td class=\"diff-context\">%d</td><td class=\"diff-context\">%d</td>"
    ix_row_same: str = "<td>%d</td><td></td>"
    ix_row_a: str = "<td class=\"diff-rm\">%d</td><td></td>"
    ix_row_b: str = "<td></td><td class=\"diff-add\">%d</td>"

    data_row_none: str = "<td></td>"
    data_row_context: str = "<td class=\"diff-context\">%s</td>"
    data_row_same: str = "<td>%s</td>"
    data_row_a: str = "<td class=\"diff-rm\">%s</td>"
    data_row_b: str = "<td class=\"diff-add\">%s</td>"

    row_head: str = "<tr>"
    row_spacer: str = ""
    row_tail: str = "</tr>"

    hline: str = ""
    elli: str = "…"


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

    def print_hello(self):
        pass

    def print_goodbye(self):
        pass

    def print_diff(self, diff: AnyDiff):
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
        elif isinstance(diff, MIMEDiff):
            self.print_mime(diff)
        elif isinstance(diff, CompositeDiff):
            for _d in diff.items:
                self.print_diff(_d)
        else:
            raise NotImplementedError(f"unknown diff: {diff}")

    def print_equal(self, diff: AnyDiff):
        raise NotImplementedError

    def print_path(self, diff: PathDiff):
        raise NotImplementedError

    def print_delta(self, diff: DeltaDiff):
        raise NotImplementedError

    def print_mime(self, diff: MIMEDiff):
        raise NotImplementedError

    def print_text(self, diff: TextDiff):
        raise NotImplementedError

    def print_table(self, diff: TableDiff):
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

    def print_hello(self):
        self.printer.write(self.text_formats.hello)

    def print_goodbye(self):
        self.printer.write(self.text_formats.goodbye)

    def print_equal(self, diff: AnyDiff):
        """
        Prints equal (empty) diff.

        Parameters
        ----------
        diff
            A diff to process.
        """
        p = self.printer.write
        add = ""
        if self.verbosity >= 1 and isinstance(diff, PathDiff) and diff.message is not None:
            add = f" ({diff.message})"
        p(self.text_formats.same_entry % f"{diff.name} -- {diff.__class__.__name__}{add}\n")

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
        if v >= 1:
            if isinstance(diff, (TableDiff, TextDiff)):
                p(f" (ratio={diff.data.ratio:.4f})")
        if v >= 2:
            if isinstance(diff, TableDiff):
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

    def print_mime(self, diff: MIMEDiff):
        """
        Print a MIME diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        self.printer.write(f"{self.text_formats.mime_entry % (diff.name, diff.mime_a, diff.mime_b)}\n")

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
        self.printer.write(self.table_formats.table_head)

        # hide columns (optionally)
        if self.table_collapse_columns:
            show_col = [True, *~diff.data.eq.all(axis=0)]
            if diff.columns is not None:
                show_col = [True, *(
                    i or col_a != col_b
                    for i, col_a, col_b in zip(show_col[1:], diff.columns.a, diff.columns.b)
                )]
        else:
            show_col = [True] * (diff.data.eq.shape[1] + 1)
        table = Table(column_mask=show_col)

        # print column names
        if diff.columns is not None:
            row = [self.table_formats.ix_row_header]
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
                    any_row_b = False
                    if i.ix_a != i.ix_b:
                        row_a.append(self.table_formats.ix_row_a % (i.ix_a,))
                        row_b.append(self.table_formats.ix_row_b % (i.ix_b,))
                        any_row_b = True
                    else:
                        row_a.append(self.table_formats.ix_row_same % (i.ix_a,))
                        row_b.append(self.table_formats.ix_row_none)
                    for a, b, eq in zip(i.a, i.b, i.diff):
                        if eq:
                            row_a.append(self.table_formats.data_row_same % (a,))
                            row_b.append(self.table_formats.data_row_none)
                        else:
                            if a:
                                row_a.append(self.table_formats.data_row_a % (a,))
                                if b:
                                    row_b.append(self.table_formats.data_row_b % (b,))
                                    any_row_b = True
                                else:
                                    row_b.append(self.table_formats.data_row_none)
                            else:
                                row_a.append(self.table_formats.data_row_b % (b,) if b else self.table_formats.data_row_none)
                                row_b.append(self.table_formats.data_row_none)
                    table.append_row(row_a)
                    if any_row_b:
                        table.append_row(row_b)

        widths = None
        # trim table width
        if self.width and self.table_formats.align:
            min_width = 1
            widths = table.get_full_widths(min_width)
            head_len = visible_len(self.table_formats.row_head)
            spacer_len = visible_len(self.table_formats.row_spacer)
            tail_len = visible_len(self.table_formats.row_tail)
            # adjustable width excludes spacer, head, tail, index column and minimal width
            adj_width = max(0, self.width - head_len - tail_len - (len(widths) - 1) * (min_width + spacer_len) - widths[0])

            cs = [0]  # np.cumsum
            s = 0
            for w in widths[1:]:
                s += w - min_width
                cs.append(s)
            if s > adj_width:
                ratio = adj_width / s
                cs = [int(i * ratio) for i in cs]
            widths = [widths[0], *(j - i + min_width for i, j in zip(cs[:-1], cs[1:]))]

        for row in table.compute(self.table_formats.row_spacer, widths=widths, elli=self.table_formats.elli):
            self.printer.write(self.table_formats.row_head + row + self.table_formats.row_tail + "\n")

        self.printer.write(self.table_formats.table_tail)


@dataclass
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
            p(self._empty_fmt.format("0", "", "", "", f"{diff.name} do not match"))
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

    def print_mime(self, diff: MIMEDiff):
        """
        Print a MIME diff.

        Parameters
        ----------
        diff
            The diff to print.
        """
        self.printer.write(self._empty_fmt.format("MIME", "", "", "", f"{diff.name} {diff.mime_a} ≠ {diff.mime_b}\n"))

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
