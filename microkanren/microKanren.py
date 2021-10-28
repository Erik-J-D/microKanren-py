import inspect
from functools import reduce
from typing import Any, Callable, Optional, Union

from more_itertools import collapse
from mypy_extensions import VarArg


class Var(str):
    pass


term = Union[Var, Any]
substitutions = dict[Var, term]

# This type isn't exactly right. A stream can be either a list of substitutions
# and nullary functions that will return a stream, or a nullary function that
# when evaluated returns a stream. Mypy doesn't like this recursive definition.
# stream = Union[list[Union[list[substitutions], Callable[[], 'stream']]], Callable[[], 'stream']]
stream = Union[list[substitutions], Any]
goal = Callable[[substitutions], stream]


def walk(t: term, subs: substitutions) -> term:
    if isinstance(t, Var) and t in subs:
        return walk(subs[t], subs)
    return t


def extend_subs(source: Var, target: Any, subs: substitutions) -> substitutions:
    return subs | {source: target}


def eq(u: term, v: term) -> goal:
    def _eq(subs: substitutions):
        s = unify(u, v, subs)
        return [s] if s else []
    return _eq


def unify(u: term, v: term, s: substitutions) -> Optional[substitutions]:
    u_target = walk(u, s)
    v_target = walk(v, s)

    if isinstance(u_target, Var) and isinstance(v_target, Var) and u_target == v_target:
        return s
    elif isinstance(u_target, Var):
        return extend_subs(u_target, v_target, s)
    elif isinstance(v_target, Var):
        return extend_subs(v_target, u_target, s)
    elif u_target == v_target:
        return s

    return None


def fresh(f: Callable[[VarArg(term)], goal]) -> goal:
    def _fresh(subs: substitutions):
        term_names = [str(term) for term in inspect.signature(f).parameters]
        terms = [Var(term) for term in term_names]
        return f(*terms)(subs)
    return _fresh


def disj(*goals: goal) -> goal:
    if len(goals) < 2:
        raise Exception("disj needs 2 or more goals")

    def _disj(subs: substitutions):
        streams = [g(subs) for g in goals]
        return reduce(mplus, streams)
    return _disj


def conj(*goals: goal) -> goal:
    if len(goals) < 2:
        raise Exception("conj needs 2 or more goals")

    def _conj(subs: substitutions):
        return reduce(bind, goals[1:], goals[0](subs))
    return _conj


def mplus(s1: stream, s2: stream) -> stream:
    if not s1:
        return s2
    elif callable(s1):
        return lambda: mplus(s2, s1())
    else:
        return list(collapse([s1[0], mplus(s1[1:], s2)], base_type=dict))


def bind(s: stream, g: goal) -> stream:
    if not s:
        return []
    elif callable(s):
        return lambda: bind(s(), g)
    else:
        return mplus(g(s[0]), bind(s[1:], g))
