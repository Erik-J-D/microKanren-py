# MicroKanren-py

This is (yet another) python implementation of [microKanren](http://webyrd.net/scheme-2013/papers/HemannMuKanren2013.pdf). It's a reasonably 1:1 translation of the code provided in the paper, but everything has type annotations to make it more obvious what data is being passed around and how.

## Running

- clone the repo, `cd` into it
- `$ poetry install`

### Tests

```
$ poetry run pytest
```

### REPL

```
$ poetry run python

>>> from microkanren import *
```
