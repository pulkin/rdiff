# rdiff

Rich file comparison with a focus on structured and tabular data

About
-----

This a WIP implementation of Myers' algorithm for constructing meaningful diffs beyond text files.

Features
--------

`rdiff` is not a drop-in replacement for your diff tool. But it does some things nicely.

- you can use it for text file diffs as usual
- **rdiff** also supports tables
- it is pretty fast
- it exposes low-level python API to compare/align arbitrary sequences
- **rdiff** can be fine-tuned to include/exclude files, align file names through regexes, set various similarity measures

Install
-------

```commandline
pip install git+git://github.com/pulkin/rdiff.git
```

Examples
--------

### CLI

```
> rdiff a.csv b.csv
comparing .
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

- align and correspond nested sequences: strings inside a list inside another list

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
  ······a[0][0:0]≠b[2][0:1]: [] ≠ ['friends']
  ······a[0][0:2]≈b[2][1:3]: ['alice', 'bob'] ≈ ['alice2', 'bob2']
  ········a[0][0]≈b[2][1] (ratio=0.9091)  # recognizes similarity between 'alice' and 'alice2'
  ··········a[0][0][0:5]=b[2][1][0:5]: 'alice' = 'alice'
  ··········a[0][0][5:5]≠b[2][1][5:6]: '' ≠ '2'
  ········a[0][1]≈b[2][2] (ratio=0.8571)
  ··········a[0][1][0:3]=b[2][2][0:3]: 'bob' = 'bob'  # recognizes similarity between 'bob' and 'bob2'
  ··········a[0][1][3:3]≠b[2][2][3:4]: '' ≠ '2'
  ····a[1]≈b[3] (ratio=1.0000)
  ······a[1][0:1]≈b[3][0:1]: ['charlie'] ≈ ['karen']  # a lower min_ratio=0.5 results in aligning 'charlie', 'karen'
  ········a[1][0]≈b[3][0] (ratio=0.5000)
  ··········a[1][0][0:2]≠b[3][0][0:1]: 'ch' ≠ 'k'
  ··········a[1][0][2:4]=b[3][0][1:3]: 'ar' = 'ar'
  ··········a[1][0][4:6]≠b[3][0][3:3]: 'li' ≠ ''
  ··········a[1][0][6:7]=b[3][0][3:4]: 'e' = 'e'
  ··········a[1][0][7:7]≠b[3][0][4:5]: '' ≠ 'n'
  ······a[1][1:2]=b[3][1:2]: ['dan'] = ['dan']
  ```

TODO
----

- [ ] semi-sorted arrays
- [ ] HTML output
- [ ] fine-tuned parameters
- [ ] ETA/progress reporting
- [ ] URI/S3 support

License
-------

[LICENSE.md](LICENSE.md)
