import functools

from base_auth.utils.org import filter_org_queryset
from base_auth.utils.owner import filter_owner_queryset


def org_queryset(func):
    @functools.wraps(func)
    def wrapper(view, *args, **kwargs):
        queryset = func(view, *args, **kwargs)
        return filter_org_queryset(view.request.user, queryset)

    return wrapper


def owner_queryset(func):
    @functools.wraps(func)
    def wrapper(view, *args, **kwargs):
        queryset = func(view, *args, **kwargs)
        return filter_owner_queryset(view.request.user, queryset)

    return wrapper
