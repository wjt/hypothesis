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
        try:
            function(*example)
        except Exception:
            pass

    with collector:
        try:
            function(*example)
        except Exception:
            pass
    best_examples = {}
    pending = []
    for f in collector.executed_features:
        if f not in seen_features:
            best_examples[f] = example
            seen_features.add(f)
            pending.append(f)

    seen_locally = t.Tracker()
    for feature in pending:
        current_example = example
        improved = True
        i = 0
        while improved:
            improved = False
            for simpler in strategy.simplify(current_example):
                i += 1
                if seen_locally.track(simpler) > 1:
                    continue
                with collector:
                    try:
                        function(*strategy.copy(simpler))
                    except Exception:
                        pass
                if feature in collector.executed_features:
                    current_example = simpler
                    # print("%d: %r -> %r" % (i, example, simpler))
                    improved = True
                    break
        if tracker.track(current_example) == 1:
            print(feature, current_example)
            yield current_example


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
