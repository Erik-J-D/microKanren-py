from microkanren import conj, disj, eq, fresh, goal, term


def test_basic_unify():
    g = fresh(lambda q: eq(q, 'hello'))
    result = g({})
    assert result == [{'q': 'hello'}]


def test_disj():
    g = fresh(lambda a: disj(eq(a, 'hello'), eq(a, 'hi'), eq(a, 12)))
    result = g({})
    assert result == [
        {'a': 'hello'},
        {'a': 'hi'},
        {'a': 12}
    ]


def test_conj():
    g = conj(
        fresh(lambda a: eq(a, 'hi')),
        fresh(lambda b: eq(b, 42)),
        fresh(lambda c: eq(c, 'hello')))
    result = g({})
    assert result == [{'a': 'hi', 'b': 42, 'c': 'hello'}]


def test_disj_conj():
    g = conj(
        fresh(lambda a: eq(a, 1)),
        fresh(lambda b: disj(
            eq(b, 2),
            eq(b, 3))))
    result = g({})
    assert result == [
        {'a': 1, 'b': 2},
        {'a': 1, 'b': 3},
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
    result = fives_and_sixes({})

    five_result = {'x': '5'}
    six_result = {'x': '6'}

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
    result = g({})

    for i in range(10):
        assert result[0] == {'x': '5'}
        assert callable(result[1])
        result = result[1]()


def test_multiple_fresh_terms():
    g = fresh(lambda x, y:
              conj(eq(x, 'hello'),
                   eq(y, x)))

    result = g({})
    assert result == [{'x': 'hello', 'y': 'hello'}]


def test_name_collision():
    g = conj(
        fresh(lambda x: eq(x, 'hello')),
        fresh(lambda x: eq(x, 'bye')),
    )

    result = g({})
    assert result == [{'x': 'hello', 'x1': 'bye'}]
