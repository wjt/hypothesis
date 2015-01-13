import time
import hypothesis.strategytable as ss
import random as r
import hypothesis.internal.cover as c
import hypothesis.internal.tracker as t
from six.moves import xrange


def find_interesting_examples_once(
    function, strategy, random, tracker, seen_features, collector, end_time
):
    pv = strategy.parameter.draw(r)
    example = strategy.produce(r, pv)
    with collector:
        function(*example)
    best_examples = {}
    pending = []
    for f in collector.executed_features:
        if f not in seen_features:
            best_examples[f] = example
            seen_features.add(f)
            pending.append(f)

    for feature in pending:
        example = best_examples[feature]

        def still_interesting(x):
            with collector:
                function(*strategy.copy(x))
            for f in collector.executed_features:
                best_examples[f] = x
            return feature in collector.executed_features

        for simpler in strategy.simplify_such_that(
            example, still_interesting
        ):
            example = simpler
            if time.time() >= end_time:
                break

        if tracker.track(example) == 1:
            yield example


def find_interesting_examples(
    function, descriptor, timeout=60, search_strategies=None, random=None,
    max_examples=1000,
):
    search_strategies = search_strategies or ss.StrategyTable()
    strategy = search_strategies.strategy(descriptor)
    random = random or r.Random()
    start = time.time()
    end_time = start + timeout
    collector = c.Collector()
    tracker = t.Tracker()
    seen_features = set()

    for _ in xrange(max_examples):
        for example in find_interesting_examples_once(
            function,
            strategy, random, tracker, seen_features, collector,
            end_time,
        ):
            yield example
            if time.time() >= end_time:
                return
