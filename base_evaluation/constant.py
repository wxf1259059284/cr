# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.utils.enum import Enum

# 评估状态：待评估、确定、放弃
EvaluationStatus = Enum(
    WAIT=0,
    CONFIRM=1,
    ABANDON=2,
)

Status = Enum(
    DELETE=0,
    NORMAL=1,
)
