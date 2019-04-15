# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    REQUIRED_FIELD=_('x_required_field'),
    TRAFFIC_EVENT_NOT_FOUND=_('x_traffic_event_not_found'),
    GET_TRAFFIC_RESULT_ERROR=_('x_get_traffic_result_error')
)
