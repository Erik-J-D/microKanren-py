from dataclasses import dataclass
from typing import Any, Callable, Optional, Union, List


class var(str):
    pass


class atom(str):
    pass


term = Union[var, atom]


@dataclass
class sub:
    source: var
    target: term


@dataclass
class subs_counter:
    sub_list: list[sub]
    counter: int


# This type isn't exactly right. A stream can be either a list of sub_counter
# and nullary functions that will return a stream, or a nullary function that
# when evaluated returns a stream. Mypy doesn't like this recursive definition.
# stream = Union[list[Union[subs_counter, Callable[[], 'stream']]], Callable[[], 'stream']]
stream = Union[list[subs_counter], Any]

goal = Callable[[subs_counter], stream]


def flatten_stream(li: list[Any]) -> stream:
    flat = []
    for i in li:
        if isinstance(i, list):
            flat.extend(i)
        else:
            flat.append(i)
    if len(flat) == 1 and callable(flat[0]):
        print("returning callable")
        return flat[0]
    return flat


def walk(t: term, sub_list: list[sub]) -> term:
    if isinstance(t, var):
        for s in sub_list:
            if t == s.source:
                return walk(s.target, sub_list)
    return t


def extend_subs(source: var, target: term, sub_list: list[sub]) -> list[sub]:
    return sub_list + [sub(source, target)]


def eq(u: term, v: term) -> goal:
    def _eq(s_c: subs_counter):
        s = unify(u, v, s_c.sub_list)
        if s:
            return [subs_counter(s, s_c.counter)]
        else:
            return []
    return _eq


def unify(u: term, v: term, s: list[sub]) -> Optional[list[sub]]:
    u = walk(u, s)
    v = walk(v, s)

    if isinstance(u, var) and isinstance(v, var) and u == v:
        return s
    elif isinstance(u, var):
        return extend_subs(u, v, s)
    elif isinstance(v, var):
        return extend_subs(v, u, s)
    elif u == v:
        return s

    return None


def fresh(f: Callable[[List[term]], goal]) -> goal:
    import inspect
    def _fresh(s_c: subs_counter):
        term_names = [str(term) for term in inspect.signature(f).parameters]
        terms = [var(term + str(s_c.counter + i)) for (i, term) in enumerate(term_names)]
        return f(*terms)(subs_counter(s_c.sub_list, s_c.counter + len(term_names)))
    return _fresh


def disj(g1: goal, g2: goal) -> goal:
    def _disj(s_c: subs_counter):
        return mplus(g1(s_c), g2(s_c))
    return _disj


def conj(g1: goal, g2: goal) -> goal:
    def _conj(s_c: subs_counter):
        return bind(g1(s_c), g2)
    return _conj


def mplus(s1: stream, s2: stream) -> stream:
    if not s1:
        return s2
    elif callable(s1):
        return lambda: mplus(s2, s1())
    else:
        return flatten_stream([s1[0], mplus(s1[1:], s2)])


def bind(s: stream, g: goal) -> stream:
    if not s:
        return []
    elif callable(s):
        return lambda: bind(s(), g)
    else:
        return mplus(g(s[0]), bind(s[1:], g))
