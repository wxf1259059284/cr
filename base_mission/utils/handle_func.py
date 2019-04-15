# -*- coding: utf-8 -*-
import json
from rest_framework import exceptions
from base_mission.error import error


def check_required_valid(data, required_fields):
    for field in required_fields:
        if data.get(field) is None or data.get(field) == '':
            raise exceptions.ValidationError({field: error.REQUIRED_FIELD})


def get_target_fields(data, fields=None, func_fields=None):
    target_dict = dict()
    if fields is None:
        fields = []

    if func_fields is None:
        func_fields = dict()

    for field in fields:
        if isinstance(field, (str, int)):
            target_dict.update({field: data.get(field)})
        else:
            raise ValueError('Not a valid key.')

    for key, func in func_fields.items():
        target_dict.update({key: func(data)})

    return target_dict


def save_options(data):
    if data.get('option'):
        return json.dumps(data.get('option'))
    else:
        return ''
