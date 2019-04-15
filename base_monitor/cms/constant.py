# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from base.utils.enum import Enum

# 脚本文件后缀
Suffix = Enum(
    PY=0,
    SH=1
)

# 脚本类型(LOCAL：本地上报，REMOTE：远程检测)
ScriptType = Enum(
    LOCAL=0,
    REMOTE=1
)

# 状态
Status = Enum(
    DELETE=0,
    NORMAL=1,
)

REGEX = Enum(
    REGEX_TITLE=_(u'^(?![0-9]+$)[0-9a-zA-Z-_]{3,100}$'),
)
