from pathlib import Path
from typing import Optional
from collections.abc import Iterator, Sequence
import re

from .path_util import accept_all, glob_rule, iter_match
from ..contextual.base import AnyDiff
from ..contextual.path import diff_path, DeltaDiff
from ..myers import MAX_COST
from ..presentation.base import TextPrinter, SummaryTextPrinter, MarkdownTableFormats


def process_iter(
        a: Path,
        b: Path,
        includes: Sequence[tuple[bool, str]] = tuple(),
        rename: Sequence[tuple[str, str]] = tuple(),
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        mime: Optional[str] = None,
        table_drop_cols: Optional[Sequence[tuple[str, list[str]]]] = None,
        sort: bool = False,
) -> Iterator[AnyDiff]:
    """
    Process anc compare to folders. Yields all diffs processed, even if they are equal.

    Parameters
    ----------
    a
        The first file/folder path.
    b
        The second file/folder path.
    includes
        A sequence of include/exclude rules as (flag, pattern) tuples.
    rename
        A sequence with rename rules as (pattern, replacement) tuples.
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
    mime
        The MIME of the two paths.
    table_drop_cols
        Table columns to drop when comparing tables.
    sort
        If True, sorts files.

    Yields
    ------
    A diff per file pair.
    """
    rules = [glob_rule(*i) for i in includes]
    rules.append(accept_all)

    transform = None
    if rename:
        def transform(child_path: Path) -> str:
            result = str(child_path)
            for args in rename:
                result = re.sub(*args, result, count=1)
            return result

    for child_a, child_b, readable_name in iter_match(a, b, rules=rules, transform=transform, sort=sort):
        if child_a is None or child_b is None:
            yield DeltaDiff(readable_name, child_a is not None)
        else:
            yield diff_path(
                a=child_a,
                b=child_b,
                name=str(readable_name),
                mime=mime,
                min_ratio=min_ratio,
                min_ratio_row=min_ratio_row,
                max_cost=max_cost,
                max_cost_row=max_cost_row,
                table_drop_cols=table_drop_cols,
            )


def process_print(
        a: Path,
        b: Path,
        includes: Sequence[tuple[bool, str]] = tuple(),
        rename: Sequence[tuple[str, str]] = tuple(),
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        mime: Optional[str] = None,
        table_drop_cols: Optional[Sequence[tuple[str, list[str]]]] = None,
        sort: bool = False,
        output_format: Optional[str] = None,
        output_verbosity: int = 0,
        output_context_size: int = 2,
        output_table_collapse_columns: bool = False,
        output_file=None,
        output_term_width: Optional[int] = None,
) -> bool:
    """
    Process anc compare to folders. Yields all diffs processed, even if they are equal.

    Parameters
    ----------
    a
        The first file/folder path.
    b
        The second file/folder path.
    includes
        A sequence of include/exclude rules as (flag, pattern) tuples.
    rename
        A sequence with rename rules as (pattern, replacement) tuples.
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
    mime
        The MIME of the two paths.
    table_drop_cols
        Table columns to drop when comparing tables.
    sort
        If True, sorts files.
    output_format
        The format to use for printing.
    output_verbosity
        Output verbosity.
    output_context_size
        The number of context lines to wrap diffs with.
    output_table_collapse_columns
        If True, saves horizontal print space by collapsing table columns.
    output_file
        The output file.
    output_term_width
        The width of the terminal.

    Returns
    -------
    True if any meaningful diff encountered and False otherwise.
    """
    if output_format is None or output_format == "default":
        output_format = "plain"
    printer_kwargs = {
        "printer": output_file,
        "verbosity": output_verbosity,
        "width": output_term_width,
        "context_size": output_context_size,
        "table_collapse_columns": output_table_collapse_columns,
    }
    printer_class = TextPrinter
    if output_format == "plain":
        pass
    elif output_format == "summary":
        printer_class = SummaryTextPrinter
    elif output_format == "markdown" or output_format == "md":
        printer_kwargs["table_formats"] = MarkdownTableFormats
    else:
        raise ValueError(f"unknown output format: {output_format}")
    printer = printer_class(**printer_kwargs)
    any_diff = False

    for i in process_iter(
            a=a, b=b, includes=includes, rename=rename, min_ratio=min_ratio, min_ratio_row=min_ratio_row,
            max_cost=max_cost, max_cost_row=max_cost_row, mime=mime, table_drop_cols=table_drop_cols, sort=sort,
    ):
        any_diff |= i.is_eq()
        printer.print_diff(i)
    return any_diff
