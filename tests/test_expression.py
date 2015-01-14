import hypothesis.expression as expr
from hypothesis import given
from hypothesis.descriptors import just, one_of
from operator import or_, and_


@given(expr.ExpressionOf(leaf_labels=int, split_labels=just('+')))
def test_can_add_integers(ex):
    assert ex.evaluate(
        reducer=lambda _, x, y: x + y,
        mapper=lambda x: x,
    ) == sum(ex)


@given(expr.ExpressionOf(
    leaf_labels={int}, split_labels=one_of([just(or_), just(and_)])))
def test_can_join_set_operations(ex):
    all_possible_ints = ex.evaluate(
        reducer=lambda _, x, y: x | y
    )
    correct_ints = ex.evaluate(reducer=lambda t, x, y: t(x, y))
    assert correct_ints.issubset(all_possible_ints)

    def should_contain(x):
        return ex.evaluate(
            reducer=lambda t, x, y: t(x, y),
            mapper=lambda s: x in s,
        )

    for x in all_possible_ints:
        assert should_contain(x) == (x in correct_ints)
