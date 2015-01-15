import hypothesis.sequencelanguage as sequence
from hypothesis import given, assume
from hypothesis.searchstrategy import SearchStrategy, ListStrategy
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


test_table = StrategyTable()

test_table.define_specification_for_instances(
    list,
    lambda strategies, descriptor:
        ListStrategy(
            list(map(strategies.strategy, descriptor)),
            average_length=2.0
        )
)

IntExpression = ExpressionStrategy(test_table.strategy([int]))


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


@given(IntExpression)
def test_has_starting_elements(x):
    compiler = sequence.SequenceCompiler()
    assert isinstance(compiler.starting_elements(x), frozenset)


@given(IntExpression)
def test_can_differentiate_by_starting_element(x):
    compiler = sequence.SequenceCompiler()
    for c in compiler.starting_elements(x):
        assert isinstance(compiler.differentiate(x, c), sequence.Expression)


@given(IntExpression, IntExpression)
def test_can_match_empty_if_both_in_and_can(x, y):
    compiler = sequence.SequenceCompiler()
    assert compiler.can_match_empty(x & y) == (
        compiler.can_match_empty(x) & compiler.can_match_empty(y)
    )


@given([int], [int])
def test_intersection_of_distinct_literals_is_unsatisfiable(x, y):
    assume(x != y)
    compiler = sequence.SequenceCompiler()
    assert not compiler.is_satisfiable(
        sequence.literal(*x) & sequence.literal(*y)
    )


@given(IntExpression, IntExpression)
def test_or_of_satisfiable_is_satisfiable(x, y):
    compiler = sequence.SequenceCompiler()
    assume(compiler.is_satisfiable(x) or compiler.is_satisfiable(y))
    assert compiler.is_satisfiable(x | y)


@given(IntExpression)
def test_every_satisfiable_expression_matches_empty_or_has_characters(x):
    assume(sequence.SequenceCompiler().is_satisfiable(x))
    assume(not sequence.SequenceCompiler().can_match_empty(x))
    assert sequence.SequenceCompiler().starting_elements(x)


def test_empty_can_match_empty():
    assert sequence.SequenceCompiler().can_match_empty(sequence.empty())


@given(IntExpression)
def test_can_compile_expression(x):
    satisfiable = sequence.SequenceCompiler().is_satisfiable(x)
    terminal, transitions = sequence.SequenceCompiler().compile(x)
    assert len(transitions) == len(terminal)
    assert any(terminal) == satisfiable
    if satisfiable:
        assert all(term or tran for term, tran in zip(terminal, transitions))
