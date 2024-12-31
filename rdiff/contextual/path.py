from pathlib import Path
from typing import Callable, TypeVar, Optional
from dataclasses import dataclass

from .base import AnyDiff
from .text import TextDiff, diff as _diff_text
from .table import TableDiff, diff as _diff_table
from ..sequence import MAX_COST

try:
    import magic
    magic = magic.Magic(mime=True)
except ImportError:
    magic = None

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
    """
    A diff indicating that two paths are exact same or different.

    Parameters
    ----------
    name
        A name this diff belongs to.
    eq
        True if paths are the same and False otherwise.
    """


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


def diff_exact(
        a: Path,
        b: Path,
        name: str,
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
        size: int = 0x10000,
) -> PathDiff:
    """
    Compares two files exactly without computing diff at all.

    Parameters
    ----------
    a
        The first file path.
    b
        The second file path.
    name
        The name associated with this comparison.
    min_ratio
    min_ratio_row
    max_cost
    max_cost_row
        Not used.
    size
        File read buffer size.

    Returns
    -------
    A diff with a single flag telling whether two paths are the same.
    """
    with a.open("rb") as fa, b.open("rb") as fb:
        while chunk_a := fa.read(size):
            chunk_b = fb.read(size)
            if chunk_a != chunk_b:
                return PathDiff(name, False)
        if fb.read(size):
            return PathDiff(name, False)
    return PathDiff(name, True)


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
    @mime_kernel("text/csv", "application/vnd.apache.parquet", "application/vnd.apache.arrow.file")
    def diff_pd_simple(
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
        kwargs = {"sep": ",", "dtype": str, "keep_default_na": False, "na_filter": False, "encoding_errors": "replace"}
        return diff_pd(
            a=pandas.read_table(a, **kwargs),
            b=pandas.read_table(b, **kwargs),
            name=name,
            min_ratio=min_ratio,
            min_ratio_row=min_ratio_row,
            max_cost=max_cost,
            max_cost_row=max_cost_row,
            table_drop_cols=table_drop_cols,
        )

    @mime_kernel("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel",
                 "application/x-hdf5")
    def diff_pd_dict(
            a: Path,
            b: Path,
            name: str,
            min_ratio: float = 0.75,
            min_ratio_row: float = 0.75,
            max_cost: int = MAX_COST,
            max_cost_row: int = MAX_COST,
            table_drop_cols: Optional[list[str]] = None,
    ) -> list[TableDiff]:
        """
        Computes a table diff between two pandas-supported files with multiple tables.

        Parameters
        ----------
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
        kwargs = {"dtype": str, "keep_default_na": False, "na_filter": False, "sheet_name": None}
        fmt = "%s/%s"
        a = pandas.read_table(a, **kwargs)
        b = pandas.read_table(b, **kwargs)

        for dfs in a, b:
            for df in dfs.values():
                df.set_axis(map(str, df.columns), axis=1, inplace=True)
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
        return result


def diff_path(
        a: Path,
        b: Path,
        name: str,
        mime: Optional[str] = None,
        min_ratio: float = 0.75,
        min_ratio_row: float = 0.75,
        max_cost: int = MAX_COST,
        max_cost_row: int = MAX_COST,
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

    Returns
    -------
    The diff.
    """
    if mime is None:
        if magic is None:
            raise ValueError("MIME not provided: please provide mime= or install python-magic for MIME detection")
        a_mime = magic.from_file(a)
        b_mime = magic.from_file(b)
        if a_mime != b_mime:
            return PathDiff(name, a_mime, b_mime, False)
        mime = a_mime
    kernel = mime_dispatch.get(mime, diff_exact)
    return kernel(a, b, name, min_ratio=min_ratio, min_ratio_row=min_ratio_row, max_cost=max_cost,
                  max_cost_row=max_cost_row)
