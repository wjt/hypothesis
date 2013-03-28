from hypothesis.expressioncompiler import Expression

def test_alternation_matches_empty_if_either_half_does():
    for s in ["()|foo", "()|()", "foo|()"]:
        assert Expression.parse(s).matches_empty()

def test_self_alternation_produces_same_dfa():
    for s in ["foo"]:
        sa = "(%s)|(%s)" % (s,s)
        assert Expression.parse(sa).dfa() == Expression.parse(s).dfa()

def test_simple_strings_have_singleton_languages():
    assert Expression.parse("foo").language_size() == 1
    assert Expression.parse("").language_size() == 1
    assert Expression.parse("a").language_size() == 1

def test_all_alternatives_appear_in_language():
    assert Expression.parse("foo|bar|baz").language_size() == 3
    assert Expression.parse("foo|foo|bar|baz").language_size() == 3
