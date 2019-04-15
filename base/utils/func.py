import copy


def default_func(*args, **kwargs):
    pass


def get_default_func():
    return copy.deepcopy(default_func)
