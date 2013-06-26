class Collector(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.examples_found = 0

    def example_found(self, value):
        self.examples_found += 1

    def example_rejected(self, value):
        pass

    def example_reduced(self, value, minimized_value):
        pass
