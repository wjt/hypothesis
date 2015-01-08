import time
import hypothesis.searchstrategy as ss
import random as r
import hypothesis.internal.cover as c
import hypothesis.internal.tracker as t
from six.moves import xrange


def find_interesting_examples(
    function, descriptor, timeout=60, search_strategies=None, random=None,
    max_examples=100, min_fails_to_change=5,
):
    timeout = float(timeout)
    search_strategies = search_strategies or ss.SearchStrategies()
    strategy = search_strategies.strategy(descriptor)
    random = random or r.Random()
    start = time.time()
    collector = c.Collector()
    tracker = t.Tracker()
    minteresting = {}

    def update_minteresting(f, example):
        if f not in minteresting:
            minteresting[f] = example
            return True
        else:
            existing = minteresting[f]
            if strategy.complexity(example) < strategy.complexity(existing):
                minteresting[f] = example
                return True
            return False

    for _ in xrange(max_examples):
        if time.time() >= start + timeout / 2:
            break
        pv = strategy.parameter.draw(r)
        example = strategy.produce(r, pv)
        with collector:
            function(*example)
        pending = []
        for f in collector.executed_features:
            update_minteresting(f, example)

    pending = list(minteresting.items())
    while pending:
        old_pending = pending
        pending = []

        for feature, example in old_pending:
            def still_interesting(x):
                with collector:
                    function(*x)
                for f in collector.executed_features:
                    if update_minteresting(f, x):
                        pending.append((f, x))
                return feature in collector.executed_features

            for simpler in strategy.simplify_such_that(
                example, still_interesting
            ):
                example = simpler
                if time.time() >= start + timeout:
                    break

            if tracker.track(example) == 1:
                yield example
