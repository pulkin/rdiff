# rdiff

Rich file comparison with a focus on structured and tabular data

![mosaic-edit](https://raw.githubusercontent.com/pulkin/rdiff/master/img/diff-mosaic-edit.png)

About
-----

`rdiff` (`richdiff` on pypi) is a diff tool and a library. You can use it to build diffs and compare strings, sequences,
arrays, nested sequences, matrices, texts, tables, files, etc. It runs Myers diff algorithm under the hood. Implemented
in python+Cython.

Features
--------

`rdiff` is not a drop-in replacement for your diff tool. But it does some things nicely.

- You can use it for text as usual.
- **rdiff** supports tables
- pretty fast
- exposes low-level python API to compare/align arbitrary sequences
- The CLI **rdiff** tool can be used to compare entire directories while discovering file types on the fly. 
  It can be fine-tuned to include/exclude files, align file names through regexes, set various similarity measures,
  provide colored reports in various formats.

Install
-------

```python
pip install richdiff
```

Install the latest git version

```commandline
pip install git+https://github.com/pulkin/rdiff.git
```

Examples
--------

### CLI

```
> rdiff a.csv b.csv
comparing a.csv vs b.csv
  Country     Region Date       Kilotons of Co2 Metric Tons Per Capita
- ----------- ------ ---------- --------------- ----------------------
(3 row(s) match)
3 Afghanistan Asia   01-01-2019 6080            0.16                  
4 Afghanistan Asia   01-01-2018 6070            0.17                  
5 Afghanistan Asia   01-01-2013 ---5990---      0.19                  
                                +++6000+++                            
6 Afghanistan Asia   01-01-2015 5950            0.18                  
7 Afghanistan Asia   01-01-2016 5300            0.15                  
(1 row(s) match)
```

### API

```python
from rdiff.sequence import diff

print(diff(
    ['apples', 'bananas', 'carrots', 'dill'],
    ['apples', 'carrots', 'dill', 'eggplant']
).to_string())
```

```text
a≈b (ratio=0.7500)
··a[0:1]=b[0:1]: ['apples'] = ['apples']
··a[1:2]≠b[1:1]: ['bananas'] ≠ []
··a[2:4]=b[1:3]: ['carrots', 'dill'] = ['carrots', 'dill']
··a[4:4]≠b[3:4]: [] ≠ ['eggplant']
```

### More examples

#### Align and correspond nested sequences: strings inside a list inside another list

```python
from rdiff.sequence import diff_nested

print(diff_nested(
    [["alice", "bob"], ["charlie", "dan"]],
    [0, 1, ["friends", "alice2", "bob2"], ["karen", "dan"]],
    min_ratio=0.5,
).to_string())
```

```text
a≈b (ratio=0.6667)
··a[0:0]≠b[0:2]: [] ≠ [0, 1]
··a[0:2]≈b[2:4]: [['alice', 'bob'], ['charlie', 'dan']] ≈ [['friends', 'alice2', 'bob2'], ['karen', 'dan']]
····a[0]≈b[2] (ratio=0.8000)  # recognizes partially aligned ["alice", "bob"] and ["friends", "alice2", "bob2"]
(...)
········a[0][0]≈b[2][1] (ratio=0.9091)  # recognizes similarity between 'alice' and 'alice2'
··········a[0][0][0:5]=b[2][1][0:5]: 'alice' = 'alice'
··········a[0][0][5:5]≠b[2][1][5:6]: '' ≠ '2'
········a[0][1]≈b[2][2] (ratio=0.8571)  # recognizes similarity between 'bob' and 'bob2'
··········a[0][1][0:3]=b[2][2][0:3]: 'bob' = 'bob'
··········a[0][1][3:3]≠b[2][2][3:4]: '' ≠ '2'
(...)
```

#### Align numpy matrices

Given two 2D arrays, compute aligned rows and columns

```python
import numpy as np
from rdiff.numpy import diff_aligned_2d

a = np.array([[0, 1], [2, 3]])
b = np.array([[0, 1, 4], [7, 8, 9], [2, 3, 6]])
# a is a "sub-matrix" of b

d = diff_aligned_2d(a, b, -1, min_ratio=0.5)
```

Inflated versions of the two matrices (`-1` from the above is a fill value)

```python
print(d.a)
print(d.b)
```

```
[[ 0  1 -1]
 [-1 -1 -1]  < an empty row needs to be added to a to align with b
 [ 2  3 -1]]
        ^^
# an empty column needs to be added as well
 
# inflated version of b is b itself in this case
[[0 1 4]
 [7 8 9]
 [2 3 6]]
```

License
-------

[LICENSE.md](LICENSE.md)
