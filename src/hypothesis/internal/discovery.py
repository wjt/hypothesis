import inspect
from hypothesis.internal.tracker import Tracker
from collections import namedtuple


Discovery = namedtuple('Discovery', (
    'module', 'name', 'descriptor', 'verifier', 'function'
))


def collect_hypothesis_functions(modules):
    if inspect.ismodule(modules):
        modules = (modules,)
    seen = Tracker()
    for m in modules:
        for k, f in vars(m).items():
            if (
                inspect.isfunction(f) and
                hasattr(f, 'hypothesis_descriptor') and
                seen.track(f) == 1
            ):
                yield Discovery(
                    m, k, f.hypothesis_descriptor, f.hypothesis_verifier,
                    f.underlying_function
                )
