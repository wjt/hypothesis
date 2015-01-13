from hypothesis import Verifier, Unfalsifiable, Settings
from random import Random


def produce_example(seed):
    v = Verifier(random=Random(seed), settings=Settings(max_examples=100))
    examples = []

    def f(xs):
        examples.append(xs)
        return True
    try:
        v.falsify(f, [int])
    except Unfalsifiable:
        pass
    return examples


def test_verifiers_produce_the_same_results_given_seed():
    assert produce_example(1) == produce_example(1)


def test_verifiers_produce_different_results_given_different_seeds():
    assert produce_example(1) != produce_example(111)
