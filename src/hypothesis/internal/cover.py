from coverage.control import coverage


class Collector(object):
    def __init__(self):
        self.known_files = {}
        self.executed_features = set()

    def __enter__(self):
        self.coverage = coverage(branch=True)
        self.coverage.start()
        self.executed_features = set()

    def __exit__(self, exc_type, exc_value, traceback):
        coverage = self.coverage
        self.coverage = None
        coverage.stop()
        coverage._harvest_data()
        for filename, arcs in coverage.data.arcs.items():
            fileid = self.file_id(filename)
            for a in arcs:
                self.executed_features.add((fileid,) + a)

    def file_id(self, filename):
        return self.known_files.setdefault(len(self.known_files) + 1)
