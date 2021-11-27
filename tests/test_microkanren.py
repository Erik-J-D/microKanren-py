from collections import Counter

from microkanren import State, conj, disj, eq, fresh, goal, term


def test_basic_unify():
    g = fresh(lambda q: eq(q, 'hello'))
    result = g(State.empty())
    assert result == [State({'q#1': 'hello'}, Counter(q=1))]

    g2 = fresh(lambda q: conj(
        eq(q, 'hello'),
        eq(q, 'fail me')
    ))
    result2 = g2(State.empty())
    assert result2 == []


def test_disj():
    g = fresh(lambda a: disj(eq(a, 'hello'), eq(a, 'hi'), eq(a, 12)))
    result = g(State.empty())
    assert result == [
        State({'a#1': 'hello'}, Counter(a=1)),
        State({'a#1': 'hi'}, Counter(a=1)),
        State({'a#1': 12}, Counter(a=1))
    ]


def test_conj():
    g = conj(
        fresh(lambda a: eq(a, 'hi')),
        fresh(lambda b: eq(b, 42)),
        fresh(lambda c: eq(c, 'hello')))
    result = g(State.empty())
    assert result == [State({'a#1': 'hi', 'b#1': 42, 'c#1': 'hello'},
                            Counter(a=1, b=1, c=1))]


def test_disj_conj():
    g = fresh(lambda a, b: conj(
        eq(a, 1),
        disj(
            eq(b, 2),
            eq(b, 3))))
    result = g(State.empty())
    assert result == [
        State({'a#1': 1, 'b#1': 2}, Counter(a=1, b=1)),
        State({'a#1': 1, 'b#1': 3}, Counter(a=1, b=1)),
    ]


def test_inverse_eta_delay():

    def fives(x: term) -> goal:
        return disj(
            eq(x, '5'),
            lambda subs: (lambda: fives(x)(subs)))

    def sixes(x: term) -> goal:
        return disj(
            eq(x, '6'),
            lambda subs: (lambda: sixes(x)(subs)))

    fives_and_sixes = fresh(lambda x: disj(fives(x), sixes(x)))
    result = fives_and_sixes(State.empty())

    five_result = State({'x#1': '5'}, Counter(x=1))
    six_result = State({'x#1': '6'}, Counter(x=1))

    assert result[0] == five_result
    assert result[2] == six_result
    assert callable(result[1])
    assert callable(result[3])

    five_branch = result[1]
    six_branch = result[3]

    five_res = five_branch()
    assert five_res[0] == five_result
    assert callable(five_res[1])

    six_res = six_branch()
    assert six_res[0] == six_result
    assert callable(six_res[1])


def test_fives():

    def fives(x: term) -> goal:
        return disj(
            eq(x, '5'),
            lambda subs: (lambda: fives(x)(subs)))

    g = fresh(fives)
    result = g(State.empty())

    for i in range(10):
        assert result[0] == State({'x#1': '5'}, Counter(x=1))
        assert callable(result[1])
        result = result[1]()


def test_multiple_fresh_terms():
    g = fresh(lambda x, y:
              conj(eq(x, 'hello'),
                   eq(y, x)))

    result = g(State.empty())
    assert result == [State({'x#1': 'hello', 'y#1': 'hello'}, Counter(x=1, y=1))]


def test_name_collision():
    g = conj(
        fresh(lambda x: eq(x, 'hello')),
        fresh(lambda x: eq(x, 'bye')),
    )

    result = g(State.empty())
    assert result == [State({'x#1': 'hello', 'x#2': 'bye'}, Counter(x=2))]

    g2 = disj(
        fresh(lambda x: conj(
            eq(x, 0),
            eq(x, 1))),
        fresh(lambda x: eq(x, 2)))

    result = g2(State.empty())
    assert result == [State({'x#2': 2}, Counter(x=2))]
