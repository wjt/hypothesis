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

    def insufficient_examples(self, hypothesis):
        pass

    def unable_to_falsify(self, hypothesis):
        pass

    def hypothesis_falsified(self, hypothesis, example):
        pass


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

    def insufficient_examples(self, hypothesis):
        self.logger.info(
            "Unable to find sufficient examples to falsify"
            " hypothesis %s. %d accepted. %d rejected" % (
                hypothesis,
                self.examples_found,
                self.examples_rejected
            ))

    def unable_to_falsify(self, hypothesis):
        self.logger.info(
            "Unable to falsify hypothesis %s"
            "after %d examples (%d rejected)" % (
                hypothesis,
                self.examples_found,
                self.examples_rejected
            ))

    def hypothesis_falsified(self, hypothesis, example):
        self.logger.info(
            "Falsified hypothesis %s with example %s"
            "after %d examples (%d rejected)" % (
                hypothesis,
                repr(example),
                self.examples_found,
                self.examples_rejected
            ))

