from hypothesis.searchstrategy import (
    strategy_for, 
    MappedSearchStrategy, 
    SearchStrategy, 
    one_of,
    just
)
from hypothesis.verifier import Verifier
from hypothesis.testdecorators import given
from collections import namedtuple
from itertools import islice

Descriptor = namedtuple("Descriptor", "descriptor")

@strategy_for(Descriptor)
class DescriptorStrategy(MappedSearchStrategy):
    def __init__(   self,
                    strategies,
                    descriptor,
                    **kwargs):
        SearchStrategy.__init__(self, strategies, descriptor,**kwargs)

        simple_descriptors = one_of(map(just, [int,float,bool,str,complex]))
        more_complex_descriptors = one_of([simple_descriptors, [simple_descriptors]])
        tuple_descriptors = one_of([(more_complex_descriptors,) * n for n in range(11)])
        self.mapped_strategy = strategies.strategy(one_of([tuple_descriptors, more_complex_descriptors]))

    def pack(self, x):
        return Descriptor(x)

    def unpack(self, x):
        return x.descriptor

StrategyAndValue = namedtuple("StrategyAndValue", ("strategy", "value"))

@strategy_for(StrategyAndValue)
class StrategyAndValueStrategy(SearchStrategy):
    def __init__(   self,
                    strategies,
                    descriptor,
                    **kwargs):
        SearchStrategy.__init__(self, strategies, descriptor,**kwargs)
        self.strategies = strategies
        self.descriptor_strategy = strategies.strategy(Descriptor)

    def produce(self, size, flags):
        strat = self.strategies.strategy(self.descriptor_strategy.produce(0.25 * size, flags).descriptor)
        value = strat.produce(0.75 * size, flags)
        return StrategyAndValue(strat, value)

    def complexity(self, x):
        return (self.descriptor_strategy.complexity(x.strategy.descriptor) +
                x.strategy.complexity(x.value))

    def simplify(self, x):
        for yv in x.strategy.simplify(x.value):
            yield StrategyAndValue(x.strategy, yv)


@given(StrategyAndValue)
def test_simplify_does_not_increase_complexity(sav):
    strat = sav.strategy
    x = sav.value
    for y in islice(strat.simplify(x),0,10):
        assert strat.complexity(y) <= strat.complexity(x)
    


