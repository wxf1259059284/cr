# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    REQUIRED_FIELD=_('x_required_field'),
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    TRAFFIC_ERROR=_('x_traffic_error'),
    NOT_FOUND=_('x_event_not_found'),
    IS_RUNNING=_('x_is_running'),
    CONNECTION_REFUSED=_('x_connection_refused'),
    UNKNOW_ERROR=_('x_unknown_error'),
    SCENE_NOT_FOUND=_('x_scene_not_found'),
    MISSING_PARAMETERS=_('x_missing_parameters'),
    INVALID_PARAMETERS=_('x_invalid_parameter'),
)
