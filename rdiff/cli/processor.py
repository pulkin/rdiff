import argparse
from collections import namedtuple
from pathlib import Path
from typing import Optional
from collections.abc import Iterator, Sequence
import re
from sys import stdout
from multiprocessing import Pool
from contextlib import nullcontext

from .path_util import accept_all, glob_rule, iter_match
from .func_util import starpartial
from ..contextual.base import AnyDiff
from ..contextual.path import diff_path
from ..myers import MAX_COST, MIN_RATIO
from ..presentation.base import (TextPrinter, SummaryTextPrinter, MarkdownTextFormats, MarkdownTableFormats,
                                 TermTextFormats, TermTableFormats, HTMLTextFormats, HTMLTableFormats)


def process_iter(
        a: Path,
        b: Path,
        includes: Sequence[tuple[bool, str]] = tuple(),
        rename: Sequence[tuple[str, str]] = tuple(),
        cherry_pick: Optional[str] = None,
        min_ratio: float = MIN_RATIO,
        min_ratio_row: float = MIN_RATIO,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        align_col_data: bool = False,
        shallow: bool = False,
        mime: Optional[str] = None,
        table_drop_cols: Optional[Sequence[str]] = None,
        table_sort: Optional[Sequence[str]] = None,
        sort: bool = False,
        pool: Optional[int] = None,
        fmt_progress: Optional[str] = None,
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
    cherry_pick
        Once set, will only consider one file matching this argument.
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
    align_col_data
        For tables, (force) compare columns by data as opposed to their names.
        This may result in much slower comparisons.
    shallow
        If True, performs a shallow comparison without building diffs at all.
    mime
        The MIME of the two paths.
    table_drop_cols
        Table columns to drop when comparing tables.
    table_sort
        Sorts tables by the columns specified.
    sort
        If True, sorts files.
    pool
        Process diffs in parallel with the specified number of processes.
    fmt_progress
        A formatting string to report progress.

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

    source = iter_match(a, b, rules=rules, transform=transform, sort=sort, cherry_pick=cherry_pick)
    if fmt_progress is not None:
        source = list(source)
    _processor = starpartial(
            diff_path,
            mime=mime,
            min_ratio=min_ratio,
            min_ratio_row=min_ratio_row,
            max_cost=max_cost,
            max_cost_row=max_cost_row,
            align_col_data=align_col_data,
            shallow=shallow,
            table_drop_cols=table_drop_cols,
            table_sort=table_sort,
    )
    if pool is not None:
        ctx = Pool(processes=pool)
    else:
        ctx = nullcontext()
    with ctx as _pool:
        if pool is not None:
            if sort:
                iterator = _pool.map(_processor, source)
            else:
                iterator = _pool.imap_unordered(_processor, source)
        else:
            iterator = map(_processor, source)
        if fmt_progress is not None:
            n = len(source)
            print(fmt_progress.format(i=0, n=n), end="", flush=True)
            for i, out in enumerate(iterator, start=1):
                print(fmt_progress.format(i=i, n=n), end="", flush=True)
                yield out
        else:
            yield from iterator


def process_print(
        a: Path,
        b: Path,
        includes: Sequence[tuple[bool, str]] = tuple(),
        rename: Sequence[tuple[str, str]] = tuple(),
        cherry_pick: Optional[str] = None,
        min_ratio: float = MIN_RATIO,
        min_ratio_row: float = MIN_RATIO,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        align_col_data: bool = False,
        shallow: bool = False,
        mime: Optional[str] = None,
        table_drop_cols: Optional[Sequence[str]] = None,
        table_sort: Optional[Sequence[str]] = None,
        sort: bool = False,
        output_format: Optional[str] = None,
        output_verbosity: int = 0,
        output_context_size: int = 2,
        output_table_collapse_columns: bool = False,
        output_file=None,
        output_term_width: Optional[int] = None,
        pool: Optional[int] = None,
        progress: bool = False,
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
    cherry_pick
        Once set, will only consider one file matching this argument.
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
    align_col_data
        For tables, (force) compare columns by data as opposed to their names.
        This may result in much slower comparisons.
    shallow
        If True, performs a shallow comparison without building diffs at all.
    mime
        The MIME of the two paths.
    table_drop_cols
        Table columns to drop when comparing tables.
    table_sort
        Sorts tables by the columns specified.
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
    pool
        Process diffs in parallel with the specified number of processes.
    progress
        If True, prints progress using built-in print function.

    Returns
    -------
    True if any meaningful diff encountered and False otherwise.
    """
    if output_file is None:
        output_file = stdout
    if output_format is None or output_format == "default":
        if hasattr(output_file, 'isatty') and output_file.isatty():
            output_format = "color"
        else:
            output_format = "plain"
    if output_format == "summary" and cherry_pick:
        output_format = "plain"  # fall back
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
        printer_kwargs["text_formats"] = MarkdownTextFormats
        printer_kwargs["table_formats"] = MarkdownTableFormats
    elif output_format == "color":
        printer_kwargs["text_formats"] = TermTextFormats
        printer_kwargs["table_formats"] = TermTableFormats
    elif output_format == "html":
        printer_kwargs["text_formats"] = HTMLTextFormats
        printer_kwargs["table_formats"] = HTMLTableFormats
    else:
        raise ValueError(f"unknown output format: {output_format}")
    printer = printer_class(**printer_kwargs)
    printer.print_hello()
    fmt_progress = None
    newline = False
    if progress:
        if output_file is stdout:
            fmt_progress = "processed {i}/{n}\n"
        else:
            fmt_progress = "\033[1K\rprocessed {i}/{n}"
            newline = True
    any_diff = False

    for i in process_iter(
            a=a, b=b, includes=includes, rename=rename, cherry_pick=cherry_pick,
            min_ratio=min_ratio, min_ratio_row=min_ratio_row,
            max_cost=max_cost, max_cost_row=max_cost_row, align_col_data=align_col_data, shallow=shallow, mime=mime,
            table_drop_cols=table_drop_cols, table_sort=table_sort, sort=sort, pool=pool, fmt_progress=fmt_progress,
    ):
        any_diff |= not i.is_eq()
        printer.print_diff(i)
    printer.print_goodbye()
    if newline:
        print("", flush=True)
    return any_diff


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.

    Parameters
    ----------
    args
        Arguments to parse.

    Returns
    -------
    A namespace with arguments.
    """

    class RepeatingOrderedAction(argparse.Action):
        def __init__(self, option_strings: list[str], dest, bucket_name: str, **kwargs):
            super().__init__(option_strings, dest, **kwargs)
            self.bucket_name = bucket_name

        def __call__(self, parser, namespace, values, option_string=None):
            bucket = getattr(namespace, self.bucket_name, [])
            bucket.append((self.dest, values))
            setattr(namespace, self.bucket_name, bucket)

    parser = argparse.ArgumentParser()
    parser.add_argument("a", type=Path, metavar="FILE", help="the A version of the file tree or a single file")
    parser.add_argument("b", type=Path, metavar="FILE", help="the B version of the file tree or a single file")
    parser.add_argument("--reverse", action="store_true", help="swap A and B")

    consumption_group = parser.add_argument_group("path consumption options")
    consumption_group.add_argument("--include", action=RepeatingOrderedAction, bucket_name="includes", metavar="PATTERN", help="paths to include")
    consumption_group.add_argument("--exclude", action=RepeatingOrderedAction, bucket_name="includes", metavar="PATTERN", help="paths to exclude")
    consumption_group.add_argument("--rename", nargs=2, action="append", metavar="PATTERN REPLACE", help="rename files using re.sub")
    consumption_group.add_argument("--sort", action="store_true", help="sort diffs by file name")
    consumption_group.add_argument("--cherry-pick", help="cherry-picks one file to diff")
    consumption_group.add_argument("--pool", type=int, metavar="NPROCS", help="compute diffs in parallel with the specified number of processes")

    algorithm_group = parser.add_argument_group("algorithm settings")
    algorithm_group.add_argument("--min-ratio", type=float, default=MIN_RATIO, metavar="[0..1]", help="the minimal required similarity ratio value. Setting this to a higher value will make the algorithm stop earlier")
    algorithm_group.add_argument("--min-ratio-row", type=float, default=MIN_RATIO, metavar="[0..1]", help="the minimal required similarity ratio value for individual lines/rows. Setting this to a higher value will make the algorithm stop earlier")
    algorithm_group.add_argument("--max-cost", type=int, default=MAX_COST, metavar="INT", help="the maximal diff cost. Setting this to a lower value will make the algorithm stop earlier")
    algorithm_group.add_argument("--max-cost-row", type=int, default=MAX_COST, metavar="INT", help="the maximal diff cost for individual lines/rows. Setting this to a lower value will make the algorithm stop earlier")
    algorithm_group.add_argument("--align-col-data", action="store_true", help="align table columns by comparing their data instead of column names. May slow down comparison significantly")
    algorithm_group.add_argument("--shallow", action="store_true", help="disables diff comparison and simply prints mismatching files")

    misc_group = parser.add_argument_group("misc settings")
    misc_group.add_argument("--mime", metavar="MIME", help="enforce the MIME")
    misc_group.add_argument("--table-drop-cols", nargs="+", metavar="COL1, COL2, ...", help="drop the specified columns from parsed tables")
    misc_group.add_argument("--table-sort", nargs="*", metavar="COL1, COL2, ...", help="sort tables by the columns specified")

    print_group = parser.add_argument_group("printing")
    print_group.add_argument("--format", choices=["plain", "md", "summary", "color", "html"], default="default", help="output print format")
    print_group.add_argument("-v", "--verbose", action="count", default=0, help="verbosity")
    print_group.add_argument("--context-size", type=int, default=2, metavar="INT", help="the number of lines/rows to surround diffs")
    print_group.add_argument("--table-collapse", action="store_true", help="hide table columns without diffs")
    print_group.add_argument("--width", type=int, metavar="INT", help="terminal width")
    print_group.add_argument("--output", type=str, metavar="FILE", help="output to file")
    print_group.add_argument("--progress", action="store_true", help="report progress")

    result = parser.parse_args(args)

    include_options_type = namedtuple("include", ("value", "what"))
    rules = getattr(result, "includes", [])
    result.includes = [
        include_options_type({"include": True, "exclude": False}[action], what)
        for action, what in rules
    ]
    del result.include
    del result.exclude

    if result.reverse:
        result.a, result.b = result.b, result.a
    del result.reverse

    return result


def run(args=None) -> bool:
    args = parse_args(args)
    with open(args.output, "w") if args.output else nullcontext() as f:
        return process_print(
            a=args.a, b=args.b,
            includes=args.includes,
            rename=args.rename,
            cherry_pick=args.cherry_pick,
            min_ratio=args.min_ratio,
            min_ratio_row=args.min_ratio_row,
            max_cost=args.max_cost,
            max_cost_row=args.max_cost_row,
            align_col_data=args.align_col_data,
            shallow=args.shallow,
            mime=args.mime,
            table_drop_cols=args.table_drop_cols,
            table_sort=args.table_sort,
            sort=args.sort,
            output_format=args.format,
            output_verbosity=args.verbose,
            output_context_size=args.context_size,
            output_table_collapse_columns=args.table_collapse,
            output_file=f,
            output_term_width=args.width,
            pool=args.pool,
            progress=args.progress,
        )


if __name__ == "__main__":
    exit(run())