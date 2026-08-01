class MatcherRegistry:

    def __init__(self):
        self._matchers = []

    def register(self, matcher):
        self._matchers.append(matcher)

    def get_matchers(self):
        return self._matchers.copy()