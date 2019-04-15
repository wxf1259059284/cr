
from django.views import defaults


class Http404Page(object):

    def __new__(cls, request, exception=None):
        exception = exception or Exception()
        return defaults.page_not_found(request, exception)


class Http403Page(object):

    def __new__(cls, request, exception=None):
        exception = exception or Exception()
        return defaults.permission_denied(request, exception)


class Http400Page(object):

    def __new__(cls, request, exception=None):
        exception = exception or Exception()
        return defaults.bad_request(request, exception)


class Http500Page(object):

    def __new__(cls, request):
        return defaults.server_error(request)
