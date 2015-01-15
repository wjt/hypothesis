import hypothesis.sequencelanguage as sequence
from hypothesis import given
from hypothesis.searchstrategy import SearchStrategy
from hypothesis.strategytable import StrategyTable
import hypothesis.params as params
from hypothesis.internal.utils.distributions import geometric
from six.moves import xrange


class ExpressionStrategy(SearchStrategy):
    descriptor = sequence.Expression

    def __init__(self, child_strategy):
        self.child_strategy = child_strategy
        self.parameter = params.CompositeParameter(
            branch_stopping_rate=params.UniformFloatParameter(0.8, 1),
            branches=params.NonEmptySubset([
                sequence.alternation,
                sequence.intersection,
                sequence.concatenation
            ]),
            singles=params.NonEmptySubset([
                sequence.repetition,
                sequence.optional,
            ]),
            child_parameter=child_strategy.parameter,
        )

    def simplify(self, value):
        for c in value.children():
            yield c
        if isinstance(value, sequence.Literal):
            values = value.values
            for s in self.child_strategy.simplify(values):
                yield sequence.literal(*s)

    def produce(self, random, pv):
        n_children = geometric(random, pv.branch_stopping_rate)
        if n_children == 0:
            return sequence.literal(
                *self.child_strategy.produce(random, pv.child_parameter)
            )
        elif n_children == 1:
            return random.choice(pv.singles)(
                self.produce(random, pv)
            )
        else:
            children = [
                self.produce(random, pv)
                for _ in xrange(n_children)
            ]
            return random.choice(pv.branches)(*children)


IntExpression = ExpressionStrategy(StrategyTable.default().strategy([int]))


@given([int])
def test_literals_are_equal(xs):
    assert sequence.literal(xs) == sequence.literal(xs)


@given(IntExpression, IntExpression, IntExpression)
def test_alternation_is_associative(x, y, z):
    assert (x | y) | z == x | (y | z)


@given(IntExpression, IntExpression, IntExpression)
def test_concatenation_is_associative(x, y, z):
    assert (x + y) + z == x + (y + z)


@given(IntExpression, IntExpression, IntExpression)
def test_intersection_is_associative(x, y, z):
    assert (x & y) & z == x & (y & z)


def test_empty_is_falsey():
    assert not sequence.empty()


@given(IntExpression)
def test_intersection_with_empty_is_empty(x):
    assert not (x & sequence.empty())


@given(IntExpression)
def test_expression_evals_correctly(x):
    y = eval(repr(x), vars(sequence))
    assert y == x


@given(IntExpression)
def test_is_hashable(x):
    assert isinstance(hash(x), int)


@given([IntExpression])
def test_hashes_correctly(xs):
    d = {}
    for x in xs:
        d[x] = x
    for x in xs:
        assert d[x] == x


@given(IntExpression)
def test_empty_is_plus_identity(x):
    assert x + sequence.empty() == x
    assert sequence.empty() + x == x
