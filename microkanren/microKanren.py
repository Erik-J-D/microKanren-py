import inspect
from collections import Counter
from functools import reduce
from typing import Any, Callable, Optional, Union

from more_itertools import collapse
from mypy_extensions import VarArg


class Var(str):
    pass


term = Union[Var, Any]
sub_dict = dict[Var, term]


class State():
    def __init__(self, subs: sub_dict, var_counter: Counter):
        self.subs = subs
        self.var_counter = var_counter

    @classmethod
    def empty(cls):
        return cls({}, Counter())

    def __eq__(self, other):
        return isinstance(other, State) and \
            self.subs == other.subs and \
            self.var_counter == other.var_counter

    def __repr__(self):
        return f"State({self.subs}, {self.var_counter})"

    def __str__(self):
        return self.__repr__(self)


# This type isn't exactly right. A stream can be either a list of States
# and nullary functions that will return a stream, or a nullary function that
# when evaluated returns a stream. Mypy doesn't like this recursive definition.
stream = Union[list[State], Any]
goal = Callable[[State], stream]


def walk(t: term, subs: sub_dict) -> term:
    if isinstance(t, Var) and t in subs:
        return walk(subs[t], subs)
    return t


def extend_subs(source: Var, target: Any, subs: sub_dict) -> sub_dict:
    return subs | {source: target}


def eq(u: term, v: term) -> goal:
    def _eq(state: State) -> stream:
        subs = unify(u, v, state.subs)
        return [State(subs, state.var_counter)] if subs else []
    return _eq


def unify(u: term, v: term, s: sub_dict) -> Optional[sub_dict]:
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
    def _fresh(state: State) -> stream:
        term_names = [str(term) for term in inspect.signature(f).parameters]
        state.var_counter.update(term_names)
        terms = [Var(f"{term}#{state.var_counter[term]}") for term in term_names]

        return f(*terms)(state)
    return _fresh


def disj(*goals: goal) -> goal:
    if len(goals) < 2:
        raise Exception("disj needs 2 or more goals")

    def _disj(state: State) -> stream:
        streams = [g(state) for g in goals]
        return reduce(mplus, streams)
    return _disj


def conj(*goals: goal) -> goal:
    if len(goals) < 2:
        raise Exception("conj needs 2 or more goals")

    def _conj(state: State) -> stream:
        return reduce(bind, goals[1:], goals[0](state))
    return _conj


def mplus(s1: stream, s2: stream) -> stream:
    if not s1:
        return s2
    elif callable(s1):
        return lambda: mplus(s2, s1())
    else:
        return list(collapse([s1[0], mplus(s1[1:], s2)]))


def bind(s: stream, g: goal) -> stream:
    if not s:
        return []
    elif callable(s):
        return lambda: bind(s(), g)
    else:
        return mplus(g(s[0]), bind(s[1:], g))
