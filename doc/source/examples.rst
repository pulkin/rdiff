Examples
========

A collection of examples covering basic usage of the package.

Compare two strings
-------------------

Let's start with producing a simple diff between two similar strings.

.. code-block:: python

    text1 = "The cat sits on the blue mat"
    text2 = "The cat sits on the red mat"

    from sdiff.sequence import diff

    text_diff = diff(text1, text2)
    print(text_diff.to_string())

The code above produces this diff:

.. code-block::

    a≈b (ratio=0.9091)
    ··a[0:20]=b[0:20]: 'The cat sits on the ' = 'The cat sits on the '
    ··a[20:23]≠b[20:21]: 'blu' ≠ 'r'
    ··a[23:24]=b[21:22]: 'e' = 'e'
    ··a[24:24]≠b[22:23]: '' ≠ 'd'
    ··a[24:28]=b[23:27]: ' mat' = ' mat'

The sequence diff object is an instance of :py:class:`sdiff.chunk.Diff`.
It wraps over two fields: the similarity ratio :py:attr:`sdiff.chunk.Diff.ratio` and the edit script
:py:attr:`sdiff.chunk.Diff.diffs`.

Similarity ratio
................

The similarity ratio is a measure of the similarity between two compared objects.
It runs from 0 (no similarity found) to 1 (objects are similar but not necessarily identical or equal).

Edit script
...........

The edit script is stored in :py:attr:`sdiff.chunk.Diff.diffs` and contains a sequence of chunks telling how
to turn the first string into the second one or the reverse.
Each chunk item is an instance of :py:class:`sdiff.chunk.Chunk` and has these three fields:

- :py:attr:`sdiff.chunk.Chunk.data_a` is a substring from the first string;
- :py:attr:`sdiff.chunk.Chunk.data_b` is a substring from the second string;
- :py:attr:`sdiff.chunk.Chunk.eq` is a bool telling whether the two substrings are equal.

For the above example, there are 5 chunks:

.. code-block:: python

    for i in text_diff.diffs: print(i)

.. code-block::

    Chunk(data_a='The cat sits on the ', data_b='The cat sits on the ', eq=True)
    Chunk(data_a='blu', data_b='r', eq=False)
    Chunk(data_a='e', data_b='e', eq=True)
    Chunk(data_a='', data_b='d', eq=False)
    Chunk(data_a=' mat', data_b=' mat', eq=True)

It is very easy to recover both strings from the above diff: you just need to concatenate all ``data_a`` substrings
to obtain ``text1`` while concatenating ``data_b`` will give you ``text2``.
This is done in :py:meth:`sdiff.chunk.Diff.get_a()` and :py:meth:`sdiff.chunk.Diff.get_b()` methods.

Compare two sequences
---------------------

We can slightly modify the above example to produce word diff, as opposed to a character diff.

.. code-block:: python

    words1 = "The", "cat", "sits", "on", "the", "blue", "mat"
    words2 = "The", "cat", "sits", "on", "the", "red", "mat"

    from sdiff.sequence import diff

    word_diff = diff(words1, words2)
    print(word_diff.to_string())

Instead of comparing individual characters, sequence differ will compare whole words while producing diffs.

.. code-block::

	a≈b (ratio=0.8571)
	··a[0:5]=b[0:5]: ('The', 'cat', 'sits', 'on', 'the') = ('The', 'cat', 'sits', 'on', 'the')
	··a[5:6]≠b[5:6]: ('blue',) ≠ ('red',)
	··a[6:7]=b[6:7]: ('mat',) = ('mat',)

You can input arbitrary objects into the comparison as long they can be compared without raising an error.

.. code-block:: python

    cat = object()
    blue = object()
    red = object()

    words1 = "The", cat, "sits", "on", "the", blue, "mat"
    words2 = "The", cat, "sits", "on", "the", red, "mat"

    word_diff = diff(words1, words2)
    print(word_diff.to_string())

.. code-block::

	a≈b (ratio=0.8571)
	··a[0:5]=b[0:5]: ('The', <object object at 0x7f66533930d0>, 'sits', 'on', 'the') = ('The', <object object at 0x7f66533930d0>, 'sits', 'on', 'the')
	··a[5:6]≠b[5:6]: (<object object at 0x7f6653393100>,) ≠ (<object object at 0x7f6653393110>,)
	··a[6:7]=b[6:7]: ('mat',) = ('mat',)

This is the hidden power of sequence differ (and the underlying Myers' algorithm): it treats comparison and similarity
as a blackbox.

Compare ignoring letter case
----------------------------

You may for example ignore letter case by supplying the ``eq=...`` argument.

.. code-block:: python

    text1 = "The cat sits on the blue mat"
    text2 = "The CAT sits on the red mat"

    from sdiff.sequence import diff

    text_diff = diff(text1, text2, eq=(text1.lower(), text2.lower()))
    print(text_diff.to_string())

Output:

.. code-block::

	a≈b (ratio=0.9091)
	··a[0:20]=b[0:20]: 'The cat sits on the ' = 'The CAT sits on the '
	...

This effectively compares lower-case versions of strings while constructing the diff object from the original.

Compare lists of numbers approximately
--------------------------------------

To do an approximate comparison of two numerical sequences you do this:

.. code-block:: python

    num1 = 0, 1, 2, 3, 4, 5
    num2 = 0, 2.1, 3.9, 5

    def eq(i, j):
        return abs(num1[i] - num2[j]) <= 0.2

    from sdiff.sequence import diff

    num_diff = diff(num1, num2, eq=eq)
    print(num_diff.to_string())

Output:

.. code-block::

	a≈b (ratio=0.8000)
	··a[0:1]=b[0:1]: (0,) = (0,)
	··a[1:2]≠b[1:1]: (1,) ≠ ()
	··a[2:3]=b[1:2]: (2,) = (2.1,)
	··a[3:4]≠b[2:2]: (3,) ≠ ()
	··a[4:6]=b[2:4]: (4, 5) = (3.9, 5)

Effectively, whenever ``eq=...`` is specified, sequence differ will not use the original objects ``num1`` and ``num2``
directly.

Nested comparison
-----------------

Another powerful feature is nested comparison using sequence diff.
It is very easy to understand it through the following snippet where we attempt to compare two nested sequences.

.. code-block:: python

    words1 = [("The", "cat"), "sits", "on", ("the", "blue", "mat")]
    words2 = [("The", "cat"), "sits", "on", ("the", "red", "mat")]

    def eq(i, j):
        w1 = words1[i]
        w2 = words2[j]
        if isinstance(w1, tuple) and isinstance(w2, tuple):
            nested_diff = diff(w1, w2, min_ratio=0.5)
            return nested_diff.ratio != 0
        return w1 == w2

    from sdiff.sequence import diff

    nested_diff = diff(words1, words2, eq=eq)
    print(nested_diff.to_string())

It outputs a fully aligned diff:

.. code-block::

	a≈b (ratio=1.0000)
	··a[0:4]=b[0:4]: [('The', 'cat'), 'sits', 'on', ('the', 'blue', 'mat')] = [('The', 'cat'), 'sits', 'on', ('the', 'red', 'mat')]

In the above, we make use of the ``min_ratio=...`` argument which you can think of as "how much similar objects are
considered equal in the outer diff?".
This argument is also useful to fine-tune the algorithm and limit its run time before it gives up.

The above implementation is obviously limited to a depth-one comparison and it does not produce diffs in subsequences.
For the fully recursive comparison experience there is :py:func:`sdiff.sequence.diff_nested`.

.. code-block:: python

    from sdiff.sequence import diff_nested

    nested_diff = diff_nested(words1, words2, min_ratio=0.5)
    print(nested_diff.to_string())

It outputs the full information on how both original sequences differ but also differences in the aligned subsequences.

.. code-block::

	a≈b (ratio=1.0000)
	··a[0:3]=b[0:3]: [('The', 'cat'), 'sits', 'on'] = [('The', 'cat'), 'sits', 'on']
	··a[3:4]≈b[3:4]: [('the', 'blue', 'mat')] ≈ [('the', 'red', 'mat')]
	····a[3]≈b[3] (ratio=0.6667)
	······a[3][0:1]=b[3][0:1]: ('the',) = ('the',)
	······a[3][1:2]≠b[3][1:2]: ('blue',) ≠ ('red',)
	······a[3][2:3]=b[3][2:3]: ('mat',) = ('mat',)

Numpy comparison
----------------

The sequence differ supports numpy out of the box alongside with the standard library ``array.array``.

.. code-block:: python

    import numpy as np

    num1 = np.arange(10)
    num2 = num1[1:-1]

    from sdiff.sequence import diff

    num_diff = diff(num1, num2)
    print(num_diff.to_string())

Outputs:

.. code-block::

	a≈b (ratio=0.8889)
	··a[0:1]≠b[0:0]: array([0]) ≠ array([], dtype=int64)
	··a[1:9]=b[0:8]: array([1, 2, 3, 4, 5, 6, 7, 8]) = array([1, 2, 3, 4, 5, 6, 7, 8])
	··a[9:10]≠b[8:8]: array([9]) ≠ array([], dtype=int64)

You can also use a dedicated wrapper which does some numpy-specific sanity checks.
It produces the same output.

.. code-block:: python

    from sdiff.numpy import diff as numpy_diff

    num_diff = numpy_diff(num1, num2)
    print(num_diff.to_string())

Matrices
........

There is a dedicated function to diff 2D numpy matrices using align-inflate algorithm (the algorithm was invented
for this package).

.. code-block:: python

    import numpy as np

    matrix1 = np.arange(9).reshape(3, 3)
    matrix2 = np.array([
        [0, 1],
        [3, 4],
        [11, 12],
        [6, 9],
    ])

    from sdiff.numpy import diff_aligned_2d

    num_diff = diff_aligned_2d(matrix1, matrix2, -1, min_ratio=0.3)

Unlike other methods, :py:func:`sdiff.numpy.diff_aligned_2d` return a different object of the type
:py:class:`sdiff.numpy.NumpyDiff`.
Fields ``num_diff.a`` and ``num_diff.b`` contain versions of the two matrices inflated towards the same size where
``-1`` was used to fill missing entries.
Field ``num_diff.eq`` contains a mask telling which inflated matrix entries are aligned.

.. code-block:: python

    print(num_diff.a)
    print(num_diff.b)
    print(num_diff.eq)

.. code-block::

	[[ 0  1  2]
	 [ 3  4  5]
	 [-1 -1 -1]
	 [ 6  7  8]]
	[[ 0  1 -1]
	 [ 3  4 -1]
	 [11 12 -1]
	 [ 6  9 -1]]
	[[ True  True False]
	 [ True  True False]
	 [False False False]
	 [ True False False]]

.. note::

    You can still use :py:func:`sdiff.numpy.diff` to compare matrices as nested sequences.
    The power :py:func:`sdiff.numpy.diff_aligned_2d` is that it looks into how rows and columns are different overall.

For more details on the algorithm and :py:class:`sdiff.numpy.NumpyDiff` objects please refer to API.

CLI Examples
============

The package provides ``sdiff`` CLI to compare files and folders.
Basic usage:

.. code-block::

    sdiff file1 file2

Compare folders
---------------

``--include`` and ``--exclude`` control which files to include and exclude.
Applies to both trees being compared.

.. code-block::

    sdiff folder1 folder2 --include */ --exclude *ide/

``sdiff`` treats ``--include`` and ``--exclude`` in ``rsync``-like fashion:

- for each path, the first matching rule matters only;
- ``--include *`` is always added implicitly;
- parent folders have to be included before children are matched.

Compare with rename
-------------------

To compare files with different names you can use ``--rename PATTERN REPLACE`` option.
For example, with the following file tree

.. code-block::

    folder1
    |-- foo.txt

    folder2
    |-- bar.txt

you can rename like this:

.. code-block::

    sdiff folder1 folder2 --rename foo bar

Rename supports regular expressions and applies to both trees: it is, essentially, ``re.sub(PATTERN, REPLACE, path, count=1)``
applied to every included path.

Save diff to html and other formats
-----------------------------------

Use ``--format``:

.. code-block::

    sdiff folder1 folder2 --format html --output diff.html

Another useful format is ``--format summary`` which prints comparison summary with file names only.

Compare different formats
-------------------------

``sdiff`` uses ``libmagic`` to determine file types and to use suitable comparison protocols.
You can force text comparison using ``--mime text``.

.. code-block::

    sdiff file1.csv file2.csv --mime text

Fine-tuned comparison using CLI
-------------------------------

There are a lot more CLI arguments allowing fine control over how the comparison is performed.
For example, ``--cherry-pick NAME`` is useful if you want to re-run comparison for a single file.
``--group PATTERN`` will apply the following CLI args only to files that match the pattern.
``--pool NPROCS`` will run parallel comparison.
More arguments:

.. code-block::

    sdiff --help

    positional arguments:
      FILE                  the A version of the file tree or a single file
      FILE                  the B version of the file tree or a single file

    options:
      -h, --help            show this help message and exit
      --reverse             swap A and B

    path consumption options:
      --include PATTERN     paths to include
      --exclude PATTERN     paths to exclude
      --rename PATTERN REPLACE PATTERN REPLACE
                            rename files using re.sub
      --sort                sort diffs by file name
      --cherry-pick NAME    cherry-picks one file to diff
      --pool NPROCS         compute diffs in parallel with the specified number of processes

    grouping:
      --group PATTERN       makes other (supported) arguments following this one to apply only to files matching PATTERN

    algorithm settings:
      --min-ratio [0..1]    the minimal required similarity ratio value. Setting this to a higher value will make the algorithm stop earlier
      --min-ratio-row [0..1]
                            the minimal required similarity ratio value for individual lines/rows. Setting this to a higher value will make the algorithm stop earlier
      --max-cost INT        the maximal diff cost. Setting this to a lower value will make the algorithm stop earlier
      --max-cost-row INT    the maximal diff cost for individual lines/rows. Setting this to a lower value will make the algorithm stop earlier
      --align-col-data      align table columns by comparing their data instead of column names. May slow down comparison significantly
      --shallow             disables diff comparison and simply prints mismatching files

    misc settings:
      --mime MIME           enforce the MIME
      --table-drop-cols COL1, COL2, ... [COL1, COL2, ... ...]
                            drop the specified columns from parsed tables
      --table-sort [COL1, COL2, ... ...]
                            sort tables by the columns specified

    printing:
      --format {plain,md,summary,color,html}
                            output print format
      -v, --verbose         verbosity
      --context-size INT    the number of lines/rows to surround diffs
      --text-line-split     split aligned lines into removed and added
      --table-collapse      hide table columns without diffs
      --width INT           terminal width
      --output FILE         output to file
      --progress            report progress
      --stats               report stats after the diff is done

Use CLI in a python script
--------------------------

If you want to compare paths in a script and print the result without returning the diff you can use the CLI entry
point:

.. code-block:: python

    from sdiff.cli.processor import process_print

    assert not process_print("folder1", "folder2")

The function returns ``False`` if no diffs were found and True otherwise.
