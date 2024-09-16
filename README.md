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
  
  print(diff(['apples', 'bananas', 'carrots', 'dill'], ['apples', 'carrots', 'dill', 'eggplant']).to_string())
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

  print(diff_nested([0, 1, ["alice", "bob"]], [0, 1, ["alice2", "bob2"]]).to_string())
  ```
  
  ```text
  Diff(1.0000):
  ··a[]≈b[]: [0, 1, ['alice', 'bob']] ≈ [0, 1, ['alice2', 'bob2']]
  ····a=b: 0
  ····a=b: 1
  ····Diff(1.0000):
  ······a[]≈b[]: ['alice', 'bob'] ≈ ['alice2', 'bob2']
  ········Diff(0.9091):
  ··········a[]=b[]: 'alice' = 'alice'
  ··········a[]≠b[]: '' ≠ '2'
  ········Diff(0.8571):
  ··········a[]=b[]: 'bob' = 'bob'
  ··········a[]≠b[]: '' ≠ '2'
  ```

License
-------

[LICENSE.md](LICENSE.md)
