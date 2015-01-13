import time
from hypothesis.verifier import Verifier, Unfalsifiable, UnsatisfiedAssumption


def convert_test_function_to_falsification(arguments, test):
    def to_falsify(xs):
        testargs, testkwargs = xs
        try:
            test(*(arguments + testargs), **testkwargs)
            return True
        except UnsatisfiedAssumption as e:
            raise e
        except Exception:
            return False
    to_falsify.__name__ = test.__name__
    to_falsify.__qualname__ = getattr(
        test, '__qualname__', test.__name__)

    return to_falsify


def given(*generator_arguments, **kwargs):
    if 'verifier' in kwargs:
        verifier = kwargs.pop('verifier')
        verifier.start_time = time.time()
    elif 'verifier_settings' in kwargs:
        verifier = Verifier(settings=kwargs.pop('verifier_settings'))
    else:
        verifier = Verifier()

    def run_test_with_generator(test):
        def wrapped_test(*arguments):
            # The only thing we accept in falsifying the test are exceptions
            # Returning successfully is always a pass.
            to_falsify = convert_test_function_to_falsification(
                arguments, test)

            try:
                falsifying_example = verifier.falsify(
                    to_falsify, (generator_arguments, kwargs))[0]
            except Unfalsifiable:
                return

            # We run this one final time so we get good errors
            # Otherwise we would have swallowed all the reports of it actually
            # having gone wrong.
            test(*(arguments + falsifying_example[0]), **falsifying_example[1])
        wrapped_test.__name__ = test.__name__
        wrapped_test.__doc__ = test.__doc__
        wrapped_test.underlying_function = test
        wrapped_test.hypothesis_descriptor = (generator_arguments, kwargs)
        wrapped_test.hypothesis_verifier = verifier
        return wrapped_test
    return run_test_with_generator
