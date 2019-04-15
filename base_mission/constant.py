# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.utils.enum import Enum

# 任务类型
Type = Enum(
    EXAM=0,
    CTF=1,
    CHECK=2,
)

CheckType = Enum(
    SYSTEM=0,
    AGENT=1,
)

# 状态
Status = Enum(
    DELETE=0,
    NORMAL=1,
)

# 任务难度
Difficulty = Enum(
    INTRODUCTION=0,
    INCREASE=1,
    EXPERT=2
)

# 试卷型任务题型
TopicProblem = Enum(
    SINGLE=0,
    MULTIPLE=1,
    JUDGEMENT=2,
    SHORTQUES=3
)

# 脚本文件后缀
Suffix = Enum(
    PY=0,
    SH=1
)

# 脚本类型
ScriptType = Enum(
    LOCAL=0,
    REMOTE=1
)

# 任务状态
MissionStatus = Enum(
    COMMING=0,
    ISPROCESS=1,
    STOP=2,
    DOWN=3,  # client error
    ERROR=4,  # run error
)
