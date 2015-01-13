from hypothesis.internal.discovery import collect_hypothesis_functions
from hypothesis.internal.interestingexamples import (
    find_interesting_examples_once
)
import sys
import importlib
from random import Random
from hypothesis.internal.tracker import Tracker
import hypothesis.internal.cover as c
import time


def main():
    modules = [importlib.import_module(arg) for arg in sys.argv[1:]]
    discoveries = list(collect_hypothesis_functions(modules))
    random = Random()
    seen_examples = Tracker()
    seen_features = set()
    collector = c.Collector()
    while True:
        for d in discoveries:
            if 'test_text_addition' not in d.name:
                continue
            strategy = d.verifier.strategy_table.strategy((d.descriptor,))
            for example in find_interesting_examples_once(
                lambda ex: d.function(*ex[0], **ex[1]),
                strategy, random, seen_examples, seen_features,
                collector,
                time.time() + 60,
            ):
                print("%s:%s: %r" % (d.module.__name__, d.name, example))

if __name__ == '__main__':  # pragma: no branch
    main()  # pragma: no cover
