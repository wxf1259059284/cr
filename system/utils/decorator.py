# -*- coding: utf-8 -*-
from functools import wraps

from ..models import Status


def upgrade_status_log(func):
    @wraps(func)
    def statusLog(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            instance = kwargs.get('instance')
            instance.info = e
            instance.upgrade_status = Status.FAIL
            instance.save()

    return statusLog


def raise_error(msg='Error'):
    def run_func(func):
        @wraps(func)
        def run(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                raise Exception('{msg} : {func} : {error}'.format(
                    msg=msg,
                    func=func.__name__,
                    error=e)
                )

        return run

    return run_func
