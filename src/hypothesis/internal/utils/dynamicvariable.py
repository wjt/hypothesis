import threading
from contextlib import contextmanager


class DynamicVariable(object):
    def __init__(self, build_default):
        self.build_default = build_default
        self.data = threading.local()

    @property
    def value(self):
        try:
            return self.data.value
        except AttributeError:
            pass

        self.data.value = self.build_default()
        return self.data.value

    @value.setter
    def value(self, x):
        self.data.value = x

    @contextmanager
    def preserving_value(self):
        if hasattr(self.data, 'value'):
            existing = self.data.value
            try:
                yield
            finally:
                self.data.value = existing
        else:
            try:
                yield
            finally:
                try:
                    delattr(self.data, 'value')
                except AttributeError:
                    pass
