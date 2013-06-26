from hypothesis.verifier import Verifier, Unfalsifiable, assume
from hypothesis.collector import Collector


class TestCollector(Collector):
    def reset(self):
        Collector.reset(self)
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
