import logging


class Collector(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.examples_found = 0
        self.examples_rejected = 0
        self.examples_simplified = 0

    def example_found(self, value):
        self.examples_found += 1

    def example_rejected(self, value):
        self.examples_rejected += 1

    def example_simplified(self, value, simplified_value):
        self.examples_simplified += 1


class LoggingCollector(Collector):
    def __init__(self, logger=logging.getLogger('hypothesis')):
        super(LoggingCollector, self).__init__()
        self.logger = logger

    def example_found(self, value):
        super(LoggingCollector, self).example_found(value)
        self.logger.debug("Testing example %s" % repr(value))

    def example_rejected(self, value):
        super(LoggingCollector, self).example_rejected(value)
        self.logger.debug("Rejected example %s" % repr(value))

    def example_simplified(self, value, simplified_value):
        super(LoggingCollector, self).example_simplified(
            value,
            simplified_value)
        self.logger.debug("Simplified example %s -> %s" % (
            repr(value),
            repr(simplified_value)))
