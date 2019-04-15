# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings


def get_language_code(request):
    return getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)


def is_en(request):
    language_code = get_language_code(request)
    return language_code == 'en'


def get_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return request.META['HTTP_X_FORWARDED_FOR']
    elif 'REMOTE_ADDR' in request.META:
        return request.META['REMOTE_ADDR']
    else:
        return ''
