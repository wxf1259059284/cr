# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    MISS_PARAMETER=_("x_missing_parameter"),
    NOT_FOUND=_('x_not_find_mission'),
    IS_RUNNING=_('x_is_running'),
    CONNECTION_REFUSED=_('x_connection_refused'),
    UNKNOW_ERROR=_('x_unknown_error'),
    REQUIRED_FIELD=_('x_required_field'),
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    NOT_EXISTED=_('x_not_existed'),
    OUT_OF_RANGE=_('x_out_of_range'),
    SCENE_NOT_FOUND=_("找不到场景"),
    MISSION_STATUS_ERROR=_('任务状态错误'),
)
