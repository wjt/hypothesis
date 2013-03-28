from hypothesis.expressioncompiler import Expression, Token
from hypothesis.testdecorators import given

def test_simple_strings_have_singleton_languages():
    assert Expression.parse("foo").language_size() == 1
    assert Expression.parse("").language_size() == 1
    assert Expression.parse("a").language_size() == 1

def test_all_alternatives_appear_in_language():
    assert Expression.parse("foo|bar|baz").language_size() == 3
    assert Expression.parse("foo|foo|bar|baz").language_size() == 3

def test_can_include_escaped_characters():
    assert Expression.parse("foo\\?") == Token("foo?")
    assert Expression.parse("\\\\\\?") == Token("\\?")

def test_char_classes_produce_same_dfa_as_alteration():
    assert Expression.parse("[ab]+").dfa() == Expression.parse("(a|b)+").dfa()
    assert Expression.parse("[a-c]+").dfa() == Expression.parse("(a|b|c)+").dfa()

def test_first_string_of_singleton_language_is_that_singleton():
    assert Expression.parse("foo").nth_string(0) == "foo"

def test_alternation_produces_both_strings_in_sorted_order():
    assert Expression.parse("foo|bar").nth_string(0) == "bar"
    assert Expression.parse("foo|bar").nth_string(1) == "foo"

identifier = "[a-zA-Z0-9]*"
@given(x = identifier, y = identifier)
def test_alternation_matches_empty_if_either_half_does(x,y):
    xory = "(%s)|(%s)" % (x,y)
    assert (Expression.parse(xory).matches_empty() ==
            Expression.parse(x).matches_empty() or Expression.parse(y).matches_empty() )

def test_self_alternation_produces_same_dfa():
    for s in ["foo"]:
        sa = "(%s)|(%s)" % (s,s)
        assert Expression.parse(sa).dfa() == Expression.parse(s).dfa()
