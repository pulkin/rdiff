# rdiff

Rich file comparison with a focus on structured and tabular data

About
-----

This a WIP implementation of Myers' algorithm for constructing meaningful diffs beyond text files.

Install
-------

```commandline
pip install git+git://github.com/pulkin/rdiff.git
```

Examples
--------

### CLI

WIP

### python

- sequence comparison
  ```python
  from rdiff.sequence import diff
  
  print(diff(
      ['apples', 'bananas', 'carrots', 'dill'],
      ['apples', 'carrots', 'dill', 'eggplant']
  ).to_string())
  ```
  
  ```text
  Diff(0.7500):
  ··a[]=b[]: ['apples'] = ['apples']
  ··a[]≠b[]: ['bananas'] ≠ []
  ··a[]=b[]: ['carrots', 'dill'] = ['carrots', 'dill']
  ··a[]≠b[]: [] ≠ ['eggplant']
  ```

- nested sequences
  ```python
  from rdiff.sequence import diff_nested

  print(diff_nested(
      [0, 1, ["alice", "bob", "charlie", "dan"]],
      [0, 1, ["alice2", "bob2", "karen", "dan"]]
  ).to_string())
  ```
  
  ```text
  Diff(1.0000):
  ··a[]=b[]: [0, 1] = [0, 1]
  ··a[]≈b[]: [['alice', 'bob', 'charlie', 'dan']] ≈ [['alice2', 'bob2', 'karen', 'dan']]
  ····Diff(0.7500):
  ······a[]≈b[]: ['alice', 'bob'] ≈ ['alice2', 'bob2']
  ········Diff(0.9091):
  ··········a[]=b[]: 'alice' = 'alice'
  ··········a[]≠b[]: '' ≠ '2'
  ········Diff(0.8571):
  ··········a[]=b[]: 'bob' = 'bob'
  ··········a[]≠b[]: '' ≠ '2'
  ······a[]≠b[]: ['charlie'] ≠ ['karen']
  ······a[]=b[]: ['dan'] = ['dan']
  ```

Project scope
-------------

What is complete/planned:

Core

- [x] reference implementation in python
- [x] Cython implementation
- [x] supporting buffer protocol in Cython

Raw comparison

- [x] linear sequence comparison
- [x] nested comparison
- [x] 2D numpy comparison / matrix alignment

Context comparison

- [ ] text diffs
- [ ] table diffs

CLI

- [ ] CLI interface
- [ ] file walk
- [ ] rich terminal output
- [ ] HTML output
- [ ] fine-tuned parameters
- [ ] ETA/progress reporting
- [ ] URI/S3 support

License
-------

[LICENSE.md](LICENSE.md)
