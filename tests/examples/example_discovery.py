from hypothesis import given


def fail():
    assert False


hello_world = given(int)(lambda i: fail())


@given(str)
def want_string(x):
    pass
