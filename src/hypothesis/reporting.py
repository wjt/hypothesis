"""
Reporting interface.

Concepts:

    There are runs and events. A run contains many events. At the completion
    of a run you get information about how many events occurred during it and
    details about their behaviour. You may also get additional notes about the
    run.

    The specific details you get about events come from tags. Each event has a
    set of tags associated with it. A run's report counts how many events had
    each tag as well as the total number of events. Tags may be any hashable
    value but will typically be strings.

    A run also has notes. Notes are simply human readable text that describe
    some overall feature of the run.

    More than run may be active at a given time, however they are strictly
    nested. The following sequence of events is valid:

        Run 1 begins
        Run 2 begins
        Run 2 ends
        Run 1 ends

    The following is not:
        Run 1 begins
        Run 2 begins
        Run 1 ends
        Run 2 ends

    This is strictly enforced by a context manager interface.

    The current run is always the inner most one, and newly created events are
    associated with the current run and not any enclosing runs.

    A run is associated with a reporter. A reporter collects data about runs
    that occur in its context and generates reports at the end.

"""

from contextlib import contextmanager


@contextmanager
def new_reporter(label):
    """
    Associate a new reporter with this context.
    """
    pass


@contextmanager
def new_run(label):
    """
    All events within this context will be associated with this label.
    Corresponds to a single falsify call.
    """
    yield


@contextmanager
def new_event():
    """
    Enclose a single event within this run.
    """
    yield


def label_event(label):
    """
    Add a tag to the current event. The fraction of events in a given run
    which have each tag will be reported at the end
    """
    pass


def add_note(note):
    """
    Adds a description to the current run. This is not associated with the
    current event.
    """
