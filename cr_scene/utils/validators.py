# -*- coding: utf-8 -*-
from rest_framework import exceptions

from cr_scene.error import error


def script_validator(value):
    if '<script>alert' in value:
        raise exceptions.ValidationError(error.XSS_ATTACK)
