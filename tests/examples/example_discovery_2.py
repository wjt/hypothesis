from tests.examples.example_discovery import want_string
from hypothesis import given


def foo():
    want_string()


@given(str)
def hello_world(xs):
    pass
