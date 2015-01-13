from hypothesis.internal.utils.dynamicvariable import DynamicVariable


def test_builds_default_value():
    var = DynamicVariable(lambda: 42)
    assert var.value == 42


def test_caches_default_value():
    calls = [0]

    def produce_default():
        calls[0] += 1
        return calls[0]

    var = DynamicVariable(produce_default)
    assert var.value == 1
    assert var.value == 1


def test_preserves_value_if_called_first():
    var = DynamicVariable(lambda: 42)
    assert var.value == 42
    with var.preserving_value():
        var.value = 10
        assert var.value == 10
    assert var.value == 42


def test_preserves_value_if_not_called_first():
    var = DynamicVariable(lambda: 42)
    assert var.value == 42
    with var.preserving_value():
        var.value = 10
        assert var.value == 10
    assert var.value == 42


def test_default_is_not_called_by_set_value():
    def boom():
        assert False

    var = DynamicVariable(boom)
    var.value = 10
    assert var.value == 10


def test_default_is_not_called_by_preserving_value():
    def boom():
        assert False

    var = DynamicVariable(boom)
    with var.preserving_value():
        var.value = 10
        assert var.value == 10
