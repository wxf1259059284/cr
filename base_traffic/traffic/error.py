# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    INVALID_PARAMS=_('x_invalid_parameters'),
    FIELDS_NOT_EXIST=_('x_fields_not_exist'),
    EVENT_IN_PROGRESS=_('x_event_in_progress'),
)
