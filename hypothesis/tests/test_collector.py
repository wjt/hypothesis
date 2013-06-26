from hypothesis.verifier import Verifier, Unfalsifiable, assume, Unsatisfiable
from hypothesis.collector import LoggingCollector
import logging
from StringIO import StringIO
import pytest

logger = logging.getLogger(__name__)
logger.level = logging.INFO
logger.propagate = False
logger_output = StringIO()
logger.addHandler(logging.StreamHandler(logger_output))


def setup_function(function):
    logger_output.buf = ''


class TestCollector(LoggingCollector):
    def __init__(self):
        super(TestCollector, self).__init__(logger)

    def reset(self):
        super(TestCollector, self).reset()
        self.simplififications = []
        self.rejections = []

    def example_simplified(self, *args):
        self.simplififications.append(args)

    def example_rejected(self, *args):
        self.rejections.append(args)


def test_tracks_event_counts():
    verifier = Verifier()
    try:
        verifier.falsify(lambda x: True, int)
    except Unfalsifiable:
        pass

    assert verifier.collector.examples_found >= 10


def test_tracks_minimizations():
    verifier = Verifier(
        starting_size=100.0,
        collector=TestCollector()
    )
    verifier.falsify(lambda x: sum(x) > 7, [int])
    assert verifier.collector.simplififications


def test_tracks_rejections():
    def picky_test(x, y):
        assume(x > y)
        return True

    verifier = Verifier(collector=TestCollector())
    try:
        verifier.falsify(picky_test, int, int)
    except Unfalsifiable:
        pass

    assert verifier.collector.rejections
    for ((x, y),) in verifier.collector.rejections:
        assert x <= y


def test_logging_logs_failure():
    verifier = Verifier(logger=logger)
    with pytest.raises(Unfalsifiable):
        verifier.falsify(lambda x: True, int)

    assert 'Unable to falsify' in logger_output.getvalue()


def test_logging_logs_insufficient_examples():
    verifier = Verifier(logger=logger)
    with pytest.raises(Unsatisfiable):
        verifier.falsify(lambda x: assume(False), int)

    assert 'Unable to find sufficient examples' in logger_output.getvalue()


def test_logging_logs_successful_falsification():
    verifier = Verifier(logger=logger)
    verifier.falsify(lambda x: False, int)

    assert 'Falsified hypothesis' in logger_output.getvalue()
