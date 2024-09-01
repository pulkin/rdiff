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
  Diff(0.7500):               # 6 out of 8 tokens in both sequences were found aligned
  ··a=b: ['apples']           # ['apples'] slice of both lists is aligned
  ··a≠b: ['bananas'] ≠ []     # but ['bananas'] is misaligned with an empty slice []
  ··a=b: ['carrots', 'dill']
  ··a≠b: [] ≠ ['eggplant']
  ```

- nested sequences
  ```python
  from rdiff.sequence import diff_nested

  print(diff_nested([0, 1, ["alice", "bob"]], [0, 1, ["alice2", "bob2"]]).to_string())
  ```
  
  ```text
  Diff(1.0000):             # Diff(1.0) does not necessarily mean sequences are equal exactly
  ··a≈b:                    # it rather means that all elements can be aligned
  ····a=b 0                 # elements 1 and 2 are equal exactly
  ····a=b 1
  ····Diff(1.0000):         # element 3 can be aligned
  ······a≈b:
  ········Diff(0.9091):     # characters in "alice" and "alice2" cannot be aligned exactly
  ··········a=b: 'alice'    # (thus, Diff(0.9091))
  ··········a≠b: '' ≠ '2'   # but, as objects, they are aligned in the respecting containers
  ········Diff(0.8571):
  ··········a=b: 'bob'
  ··········a≠b: '' ≠ '2'
  ```

License
-------

[LICENSE.md](LICENSE.md)
