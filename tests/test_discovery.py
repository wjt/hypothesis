from hypothesis.internal.discovery import collect_hypothesis_functions
import tests.examples.example_discovery as example
import tests.examples.example_discovery_2 as example2


def test_discovers_a_lambda():
    discoveries = list(collect_hypothesis_functions(example))
    assert any(d.function.__name__ == '<lambda>' for d in discoveries)


def test_discovers_a_function_with_decorator():
    discoveries = list(collect_hypothesis_functions(example))
    x = next(d for d in discoveries if d.name == 'want_string')
    assert x.module == example
    assert x.descriptor == (str,)


def test_deduplicates_discoveries_by_function_not_name():
    multi_discovery = list(collect_hypothesis_functions((
        example, example2
    )))

    assert len(multi_discovery) == 3
