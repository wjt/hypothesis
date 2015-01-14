from hypothesis.searchstrategy import SearchStrategy
from hypothesis.strategytable import StrategyTable
from collections import namedtuple, Counter
import hypothesis.params as params
from hypothesis.internal.utils.distributions import biased_coin
from hypothesis.internal.utils.hashitanyway import hash_everything


class Expression(object):
    def __init__(self, index, owner):
        self._index = index
        self.owner = owner

    def evaluate(self, reducer, mapper=lambda x: x, table=None):
        if table is None:
            table = {}
        if self._index not in table:
            table[self._index] = self.do_evaluate(reducer, mapper, table)
        return table[self._index]

    def build_table(self, table=None):
        if table is None:
            table = [None] * (self._index + 1)
        if table[self._index]:
            return
        table[self._index] = self
        for c in self.each_child():
            c.build_table(table)
        return table

    @property
    def name(self):
        return "t%d" % (self._index,)

    def name_or_definition(self, refcounts):
        if refcounts[self.name] > 1:
            return self.name
        else:
            return self.simple_repr(refcounts)

    def __iter__(self):
        parts = [self]

        while parts:
            x = parts.pop()
            if isinstance(x, Split):
                parts.append(x.left)
                parts.append(x.right)
            if isinstance(x, Leaf):
                yield x.value


class Leaf(Expression):
    def __init__(self, index, owner, value):
        super(Leaf, self).__init__(index, owner)
        self.value = value

    def __repr__(self):
        return "Leaf(%r)" % (self.value,)

    def __hash__(self):
        return hash_everything(self.value)

    def __eq__(self, other):
        return (
            isinstance(other, Leaf) and
            self._index == other._index and
            self.value == other.value
        )

    def simple_repr(self, refcounts):
        return repr(self)

    def rebuild_from_table(self, table):
        return table[self._index]

    def each_child(self):
        return ()

    def unique_children(self, xs):
        return xs or set()

    def refcounts(self, counter):
        return counter or Counter()

    def do_evaluate(self, reducer, mapper, table):
        return mapper(self.value)


class Split(Expression):
    def __init__(self, index, owner, label, left, right):
        super(Split, self).__init__(index, owner)
        assert left._index < self._index
        assert right._index < self._index
        self.label = label
        self.left = left
        self.right = right

    def __hash__(self):
        if not hasattr(self, '_h'):
            self._h = (
                hash_everything(self.label) ^
                hash(self.left) ^ hash(self.right))
        return self._h

    def __eq__(self, other):
        return (
            isinstance(other, Split) and
            self._index == other._index and
            self.label == other.label and
            self.left == other.left and
            self.right == other.right
        )

    def each_child(self):
        yield self.left
        yield self.right

    def rebuild_from_table(self, table):
        return Split(
            self._index,
            self.owner,
            self.label,
            self.left.rebuild_from_table(table),
            self.right.rebuild_from_table(table),
        )

    def refcounts(self, counter=None):
        if counter is None:
            counter = Counter()
        counter[self.left.name] += 1
        counter[self.right.name] += 1
        self.left.refcounts(counter)
        self.right.refcounts(counter)
        return counter

    def unique_children(self, children=None):
        if children is None:
            children = set()
        if self in children:
            return
        self.left.unique_children(children)
        children.add(self.left)
        self.right.unique_children(children)
        children.add(self.right)
        return children

    def simple_repr(self, refcounts):
        return "Split(%r, %s, %s)" % (
            self.label,
            self.left.name_or_definition(refcounts),
            self.right.name_or_definition(refcounts),
        )

    def __repr__(self):
        children = sorted(
            self.unique_children(),
            key=lambda t: t._index,
            reverse=True
        )
        rc = self.refcounts()
        if all(rc[c.name] <= 1 for c in children):
            return self.simple_repr(rc)
        else:
            return "%s where %s" % (
                self.simple_repr(rc),
                ', '.join(
                    "%s = %s" % (
                        c.name, c.simple_repr(rc)
                    )
                    for c in children
                    if rc[c.name] > 1
                )
            )

    def do_evaluate(self, reducer, mapper, table):
        return reducer(
            self.label,
            self.left.evaluate(reducer, mapper, table),
            self.right.evaluate(reducer, mapper, table),
        )


ExpressionOf = namedtuple(
    'ExpressionOf', ('split_labels', 'leaf_labels'))


class ExpressionStrategy(SearchStrategy):
    def __init__(self, split_strategy, leaf_strategy):
        self.split_strategy = split_strategy
        self.leaf_strategy = leaf_strategy
        self.descriptor = ExpressionOf(
            split_strategy.descriptor, leaf_strategy.descriptor
        )
        self.parameter = params.CompositeParameter(
            leaf_parameter=leaf_strategy.parameter,
            split_parameter=split_strategy.parameter,
            leaf_chance=params.UniformFloatParameter(0, 1),
            stopping_chance=params.UniformFloatParameter(0.1, 1),
        )

    def produce(self, random, pv):
        results = []
        self.produce_leaf(results, random, pv)
        latest = results[0]
        while not biased_coin(random, pv.stopping_chance):
            x = latest
            if biased_coin(random, pv.leaf_chance):
                y = self.produce_leaf(results, random, pv)
            else:
                y = random.choice(results)
            if biased_coin(random, 0.5):
                x, y = y, x
            latest = Split(
                len(results), self,
                self.split_strategy.produce(random, pv.split_parameter),
                x, y
            )
            results.append(latest)
        return latest

    def produce_leaf(self, results, random, pv):
        leaf = Leaf(
            len(results), self, self.leaf_strategy.produce(
                random, pv.leaf_parameter))
        results.append(leaf)
        return leaf

    def could_have_produced(self, value):
        return isinstance(value, Expression) and (
            isinstance(value.owner, ExpressionStrategy) and
            value.owner.descriptor == self.descriptor
        )

    def simplify(self, graph):
        if isinstance(graph, Leaf):
            for v in self.leaf_strategy.simplify(graph.value):
                yield Leaf(graph._index, self, v)
        else:
            assert isinstance(graph, Split)
            yield graph.left
            yield graph.right
            for label in self.split_strategy.simplify(graph.label):
                yield Split(graph._index, self, label, graph.left, graph.right)
            table = graph.build_table()
            for i in xrange(len(table)):
                if isinstance(table[i], Leaf):
                    new_table = list(table)
                    for l in self.simplify(table[i]):
                        new_table[i] = l
                        yield graph.rebuild_from_table(new_table)

StrategyTable.default().define_specification_for_instances(
    ExpressionOf,
    lambda s, d: ExpressionStrategy(
        split_strategy=s.strategy(d.split_labels),
        leaf_strategy=s.strategy(d.leaf_labels),
    )
)
