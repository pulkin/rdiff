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
  
  diff(['apples', 'bananas', 'carrots', 'dill'], ['apples', 'carrots', 'dill', 'eggplant'])
  ```

License
-------

[LICENSE.md](LICENSE.md)
