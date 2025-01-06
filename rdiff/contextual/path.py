from pathlib import Path
from typing import Callable, TypeVar, Optional
from dataclasses import dataclass
import filecmp
from functools import partial

import pandas as pd

from .base import AnyDiff
from .text import TextDiff, diff as _diff_text
from .table import TableDiff, diff as _diff_table
from ..sequence import MAX_COST

try:
    import magic
    magic_guess_custom = magic.Magic(mime=True, magic_file=Path(__file__).parent / "magic")
except ImportError:
    magic = magic_guess_custom = None

try:
    import pandas
except ImportError:
    pandas = None


DiffKernel = Callable[[Path, Path, str], AnyDiff]
T = TypeVar("T", bound=DiffKernel)


mime_dispatch: dict[str, DiffKernel] = {}


@dataclass
class PathDiff(AnyDiff):
    eq: bool
    message: Optional[str] = None
    """
    A diff indicating that two paths are exact same or different.

    Parameters
    ----------
    name
        A name this diff belongs to.
    eq
        True if paths are the same and False otherwise.
    message
        Whatever message to share.
    """

    def is_eq(self) -> bool:
        return self.eq


@dataclass
class MIMEDiff(AnyDiff):
    mime_a: str
    mime_b: str
    """
    A diff indicating that two paths have different MIMEs.

    Parameters
    ----------
    name
        A name this diff belongs to.
    mime_a
    mime_b
        The two MIME types.
    """

    def is_eq(self) -> bool:
        return self.mime_a == self.mime_b


@dataclass
class DeltaDiff(AnyDiff):
    exist_a: bool
    """
    A diff indicating that one of the paths does not exist.

    Parameters
    ----------
    name
        A name this diff belongs to.
    exist_a
        A flag indicating that a path exists in a.
    """

    @property
    def exist_b(self) -> bool:
        return not self.exist_a

    def is_eq(self) -> bool:
        return False


@dataclass
class CompositeDiff(AnyDiff):
    items: list[AnyDiff]
    """
    A diff with multiple parts.

    Parameters
    ----------
    name
        A name this diff belongs to.
    items
        Diff parts.
    """

    def is_eq(self) -> bool:
        return all(i.is_eq() for i in self.items)


def mime_kernel(*args: str) -> Callable[[T], T]:
    """
    Associates a diff function with one or more MIME types.

    Parameters
    ----------
    args
        MIME strings.
    """
    def _decorate(kernel: T) -> T:
        for i in args:
            mime_dispatch[i] = kernel
        return kernel
    return _decorate


@mime_kernel("text/plain")
def diff_text(
        a: Path,
        b: Path,
        name: str,
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
) -> TextDiff:
    """
    Computes a text diff between two files.

    Parameters
    ----------
    a
        The first file path.
    b
        The second file path.
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
    -------
    The text diff.
    """
    with open(a, "r") as fa, open(b, "r") as fb:
        return _diff_text(list(fa), list(fb), name, min_ratio=min_ratio, min_ratio_row=min_ratio_row,
                          max_cost=max_cost, max_cost_row=max_cost_row)


def diff_pd(
        a,
        b,
        name: str,
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        table_drop_cols: Optional[list[str]] = None,
) -> TableDiff:
    """
    Computes a table diff between two ``pandas.DataFrame``.

    Parameters
    ----------
    a
        The first table.
    b
        The second table.
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
    table_drop_cols
        Columns to drop before comparing.

    Returns
    -------
    The table diff.
    """
    if table_drop_cols is not None:
        a = a.copy()
        b = b.copy()
        for df in a, b:
            df.drop(columns=table_drop_cols, inplace=True, errors="ignore")
    return _diff_table(a=a, b=b, name=name, min_ratio=min_ratio, min_ratio_row=min_ratio_row, max_cost=max_cost,
                       max_cost_row=max_cost_row)


if pandas:
    def diff_pd_simple(
            reader: Callable[[Path], pd.DataFrame],
            a: Path,
            b: Path,
            name: str,
            min_ratio: float = 0.75,
            min_ratio_row: float = 0.75,
            max_cost: int = MAX_COST,
            max_cost_row: int = MAX_COST,
            table_drop_cols: Optional[list[str]] = None,
    ) -> TableDiff:
        """
        Computes a table diff between two pandas-supported files with tables.

        Parameters
        ----------
        reader
            A reader transforming path into dataframe.
        a
            The first path with a table.
        b
            The second path with a table.
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
        table_drop_cols
            Columns to drop before comparing.

        Returns
        -------
        The table diff.
        """
        return diff_pd(
            a=reader(a),
            b=reader(b),
            name=name,
            min_ratio=min_ratio,
            min_ratio_row=min_ratio_row,
            max_cost=max_cost,
            max_cost_row=max_cost_row,
            table_drop_cols=table_drop_cols,
        )


    diff_pd_csv = mime_kernel("text/csv")(partial(diff_pd_simple, partial(pd.read_csv, dtype=str, keep_default_na=False, na_filter=False, encoding_errors="replace")))
    diff_pd_feather = mime_kernel("application/vnd.apache.arrow.file")(partial(diff_pd_simple, pd.read_feather))
    diff_pd_parquet = mime_kernel("application/vnd.apache.parquet")(partial(diff_pd_simple, pd.read_parquet))


    def diff_pd_dict(
            reader: Callable[[Path], dict[str, pd.DataFrame]],
            a: Path,
            b: Path,
            name: str,
            min_ratio: float = 0.75,
            min_ratio_row: float = 0.75,
            max_cost: int = MAX_COST,
            max_cost_row: int = MAX_COST,
            table_drop_cols: Optional[list[str]] = None,
    ) -> CompositeDiff:
        """
        Computes a table diff between two pandas-supported files with multiple tables.

        Parameters
        ----------
        reader
            A reader transforming path into a dictionary of dataframes.
        a
            The first path with tables.
        b
            The second path with tables.
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
        table_drop_cols
            Columns to drop before comparing.

        Returns
        -------
        The table diff.
        """
        fmt = "%s/%s"
        a = reader(a)
        b = reader(b)

        for dfs in a, b:
            for df in dfs.values():
                df = df.set_axis(map(str, df.columns), axis=1, copy=False)
                df.fillna("", inplace=True)

        result = []

        for i in set(a) - set(b):
            result.append(DeltaDiff(fmt % (name, i), True))
        for i in set(b) - set(a):
            result.append(DeltaDiff(fmt % (name, i), False))
        for i in set(a) & set(b):
            result.append(
                diff_pd(
                    a=a[i],
                    b=b[i],
                    name=fmt % (name, i),
                    min_ratio=min_ratio,
                    min_ratio_row=min_ratio_row,
                    max_cost=max_cost,
                    max_cost_row=max_cost_row,
                    table_drop_cols=table_drop_cols,
                )
            )
        return CompositeDiff(name, result)


    diff_pd_excel = mime_kernel("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel")(partial(diff_pd_dict, partial(pd.read_excel, dtype=str, keep_default_na=False, na_filter=False, sheet_name=None)))


def diff_path(
        a: Path,
        b: Path,
        name: str,
        mime: Optional[str] = None,
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        table_drop_cols: Optional[list[str]] = None,
) -> AnyDiff:
    """
    Computes a diff between two files based on their (common) MIME.

    Parameters
    ----------
    a
        The first file path.
    b
        The second file path.
    name
        The name associated with this comparison.
    mime
        The MIME of the two paths.
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
    table_drop_cols
        Table columns to drop when comparing tables.

    Returns
    -------
    The diff.
    """
    if filecmp.cmp(a, b, shallow=False):
        return PathDiff(name, eq=True, message="files are binary equal")
    if mime is None and magic is not None:
        a_mime = magic_guess_custom.from_file(a)
        b_mime = magic_guess_custom.from_file(b)
        if a_mime != b_mime:
            return MIMEDiff(name, a_mime, b_mime)
        mime = a_mime
    if mime is None:
        return PathDiff(name, eq=False, message=f"failed to determine MIME; tried libmagic: {magic is not None}")
    try:
        kernel = mime_dispatch[mime]
    except KeyError:
        return PathDiff(name, eq=False, message=f"unknown common MIME: {mime}")
    kwargs = {}
    if kernel in (diff_pd_csv, diff_pd_feather, diff_pd_parquet, diff_pd_excel):
        kwargs["table_drop_cols"] = table_drop_cols
    return kernel(a, b, name, min_ratio=min_ratio, min_ratio_row=min_ratio_row, max_cost=max_cost,
                  max_cost_row=max_cost_row, **kwargs)
