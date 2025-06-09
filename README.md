# sdiff

Rich file comparison with a focus on structured and tabular data

![mosaic-edit](https://raw.githubusercontent.com/pulkin/sdiff/master/img/diff-mosaic-edit.png)

About
-----

`sdiff` is a diff tool and a library. You can use it to build diffs and compare strings, sequences,
arrays, nested sequences, matrices, texts, tables, files, etc. It runs Myers diff algorithm under the hood. Implemented
in python+Cython.

Features
--------

`sdiff` is not a drop-in replacement for your diff tool. But it does some things nicely.

- You can use it for text as usual.
- **sdiff** supports tables
- pretty fast
- exposes low-level python API to compare/align arbitrary sequences
- The CLI **sdiff** tool can be used to compare entire directories while discovering file types on the fly. 
  It can be fine-tuned to include/exclude files, align file names through regexes, set various similarity measures,
  provide colored reports in various formats.

Install
-------

```python
pip install sdiff
```

Install the latest git version

```commandline
pip install git+https://github.com/pulkin/sdiff.git
```

Examples
--------

### CLI

```
> sdiff a.csv b.csv
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
from sdiff.sequence import diff

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

## Documentation

Visit [https://sdiff.readthedocs.io/en/latest/](https://sdiff.readthedocs.io/en/latest/)

License
-------

[LICENSE.md](LICENSE.md)
