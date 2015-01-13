from hypothesis.internal import cover


def boo(x):
    assert x


def test_is_interested_in_failing_assertions():
    results = []
    c = cover.Collector()

    for x in [False, False, True, True]:
        with c:
            try:
                boo(x)
            except Exception:
                pass
        results.append(c.executed_features)
    assert results[0] == results[1]
    assert results[2] == results[3]
    assert results[1] != results[2]


def boop(x):
    try:
        boo(x)
    except AssertionError:
        pass


def test_is_interested_in_caught_assertions():
    results = []
    c = cover.Collector()

    for x in [False, False, True, True]:
        with c:
            try:
                boop(x)
            except Exception:
                pass
        results.append(c.executed_features)
    assert results[0] == results[1]
    assert results[2] == results[3]
    assert results[1] != results[2]
