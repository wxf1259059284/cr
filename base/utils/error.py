# -*- coding: utf-8 -*-
import copy

from django.utils import six
from rest_framework.exceptions import ErrorDetail

from base.utils.enum import Enum
from base.utils.text import Txt, trans as _

common_error = Enum(
    ERROR=_('x_busy_server'),
    NO_PERMISSION=_('x_no_operation_permission'),
    INVALID_PARAMS=_('x_invalid_parameter'),
    INVALID_VALUE=_('x_invalid_parameter_value'),
    DUPLICATE_SUBMIT=_('x_duplicate_submission'),
    DUPLICATE_REQUEST=_('x_duplicate_request'),
    SAVE_FAILED=_('x_data_save_failed'),
)


class Error(object):
    error = Enum()

    def __new__(cls, **errors):
        custom_errors = copy.copy(common_error.source)
        for attr_name, error_desc in errors.items():
            error_code = cls.generate_error_code(attr_name)
            if isinstance(error_desc, Txt):
                error_desc.code = error_code
                detail = error_desc
            elif isinstance(error_desc, six.string_types):
                detail = ErrorDetail(error_desc, error_code)
            else:
                error_desc.code = error_code
                detail = error_desc
            custom_errors[attr_name] = detail
        cls.error.update(**custom_errors)
        return Enum(**custom_errors)

    @classmethod
    def generate_error_code(cls, attr_name):
        return attr_name


error = Error.error
