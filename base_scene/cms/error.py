# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    CONFLICT_WITH_BASE_IMAGE_NAME=_('和基础镜像名称冲突'),
    NAME_EXISTS=_('名称已存在'),
    STANDARD_DEVICE_NO_LOGO=_('标靶不能没有logo'),
    DEVICE_NO_SCENE=_('标靶没有机器'),
    TERMINAL_NOT_READY=_('终端未准备好'),
    IMAGE_SAVING=_('镜像保存中'),

    NO_SCENE_CONFIG=_('没有配置'),

    GATEWAY_NOT_FOUND=_('网关不存在'),
    TERMINAL_NOT_FOUND=_('终端不存在'),
)
