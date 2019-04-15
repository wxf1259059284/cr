#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午7:02
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : enums.py.py
# @Project : cpss

from ..consts import Enum

class EnumVirtualModelType(Enum):
    empty = 0               # 空模型
    vir_att_shipgroup = 1   # 舰队
    vir_res_asset = 2       #
    vir_att_shipleader = 3  # 旗舰
    vir_arbiter = 4         # 仲裁者
    vir_dazzle = 5          #

class EnumOjActions(Enum):
    scan = 0
    solve = 1
    ai = 2

class EnumOjColors(Enum):
    red = 0
    yellow = 1
    blue = 3
    orange = 4
    purple = 5
    green = 6
    cyan = 7
    magenta = 8
    red2 = 9
    yellow2 = 10
    blue2 = 11
    orange2 = 12
    purple2 = 13
    green2 = 14