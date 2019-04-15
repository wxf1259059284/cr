# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    AUTHENTICATION_FAILED=_('用户名或密码错误'),
    PERMISSION_NOT_ALLOWED=_('权限不允许')
)
