from microkanren import (atom, conj, disj, eq, fresh, goal, sub, subs_counter,
                         term)


def test_basic_unify():
    empty = subs_counter([], 0)
    g = fresh(lambda q: eq(q, atom("hello")))
    result = g(empty)
    assert result == [subs_counter([sub(0, 'hello')], 1)]


def test_disj():
    empty = subs_counter([], 0)
    g = fresh(lambda a: disj(eq(a, atom("hello")), eq(a, atom("hi"))))
    result = g(empty)
    assert result == [
        subs_counter([sub(0, 'hello')], 1),
        subs_counter([sub(0, 'hi')], 1)
    ]


def test_conj():
    empty = subs_counter([], 0)
    g = conj(
        fresh(lambda a: eq(a, atom("hi"))),
        fresh(lambda b: eq(b, atom("hello"))))
    result = g(empty)
    assert result == [subs_counter([sub(0, 'hi'), sub(1, 'hello')], 2)]


def test_disj_conj():
    empty = subs_counter([], 0)
    g = conj(
        fresh(lambda a: eq(a, "1")),
        fresh(lambda b: disj(
            eq(b, atom("2")),
            eq(b, atom("3")))))
    result = g(empty)
    assert result == [
        subs_counter([sub(0, '1'), sub(1, '2')], 2),
        subs_counter([sub(0, '1'), sub(1, '3')], 2),
    ]


def test_inverse_eta_delay():
    empty = subs_counter([], 0)

    def fives(x: term) -> goal:
        return disj(
            eq(x, atom("5")),
            lambda s_c: (lambda: fives(x)(s_c)))

    def sixes(x: term) -> goal:
        return disj(
            eq(x, atom("6")),
            lambda s_c: (lambda: sixes(x)(s_c)))

    fives_and_sixes = fresh(lambda x: disj(fives(x), sixes(x)))
    result = fives_and_sixes(empty)

    # should alternate between '5' and '6'
    next_sub_lookup = {'5': '6', '6': '5'}
    next_sub = '5'
    for _ in range(10):
        assert result[0] == subs_counter([sub(0, next_sub)], 1)
        assert callable(result[1])
        result = result[1]()
        next_sub = next_sub_lookup[next_sub]
