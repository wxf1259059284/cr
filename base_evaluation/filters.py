# -*- coding: utf-8 -*-
class Filter(object):
    def __init__(self):
        self._filters = set()

    def register_filter(self, func):
        self._filters.add(func)

    def unregister_filter(self, func):
        self._filters.remove(func)

    def clear_filters(self):
        self._filters.clear()

    def is_valid(self, data):
        return any(map(lambda func: func(data), self._filters))


class KeyWordFilter(object):
    def __init__(self, keywords):
        self.keywords = keywords

    def _raise_keyword_filter(self, keywords):
        if isinstance(keywords, (list, tuple, set)):
            return lambda data: all(map(lambda x: x in data, keywords))
        else:
            return lambda data: keywords in data

    def _raise_filters(self):
        return map(lambda word: self._raise_keyword_filter(word), self.keywords)

    def is_valid(self, data):
        return any(map(lambda func: func(data), self._raise_filters()))


data_filter = Filter()
data_filter.register_filter(KeyWordFilter(['服务', '木马']).is_valid)
