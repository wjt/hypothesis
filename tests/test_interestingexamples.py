from hypothesis.internal.interestingexamples import find_interesting_examples
from six.moves import xrange
from random import Random
import itertools


INSERTION_SORT_SIZE = 4


def quicksort(seed, xs):
    random = Random(seed)
    xs = list(xs)

    def swap(i, j):
        xs[i], xs[j] = xs[j], xs[i]

    def partition(lo, hi):
        pivot = random.randint(lo, hi-1)
        pivot_value = xs[pivot]
        swap(pivot, hi)
        store = lo
        for i in xrange(lo, hi):
            if xs[i] < pivot_value:
                swap(i, store)
                store += 1
        swap(store, hi)
        return store

    def insertion_sort(lo, hi):
        i = 1
        while i <= hi:
            j = i
            while j > 0:
                if xs[j-1] > xs[j]:
                    swap(j, j-1)
                    j -= 1
                else:
                    break
            i += 1

    def do_quicksort(lo, hi, depth=0):
        if hi - lo <= 1:
            return
        if hi - lo == 2:
            if xs[lo] > xs[hi]:
                swap(lo, hi)
            return
        if hi - lo <= INSERTION_SORT_SIZE or depth >= 10:
            insertion_sort(lo, hi)
            return
        if lo < hi:
            p = partition(lo, hi)
            do_quicksort(lo, p-1, depth+1)
            do_quicksort(p+1, hi, depth+1)
    do_quicksort(0, len(xs) - 1)
    return xs


def test_finds_interesting_sets():
    examples = list(itertools.islice((
        x[1]
        for x in find_interesting_examples(
            quicksort, (int, [int],), timeout=10
        )),
        5
    ))
    assert len(examples) > 4
    assert [] in examples
    assert any(len(x) > INSERTION_SORT_SIZE for x in examples)
    assert any(
        len(x) > INSERTION_SORT_SIZE and sorted(x) == x for x in examples)
    assert any(
        len(x) > INSERTION_SORT_SIZE and
        sorted(x, reverse=True) == x for x in examples)
