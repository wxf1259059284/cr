#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午6:59
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : enums.py
# @Project : cpss

from ..consts import Enum

class EnumScenarioType(Enum):
    all_scenarios = 0
    real_datacenter = 1  # 机房场景
    virtual_starwar = 2  # 太空场景

class EnumAttackIntensity(Enum):     # 攻击强度
    attack_weak = 0            # 弱
    attack_moderate = 1        # 中等
    attack_heavy = 2           # 重
    attack_charge = 3
    attack_gather = 4          # 应该是指采及集水晶

class EnumAdEffect(Enum):   # 特效类型(可以在单个物体上展示的特效)
    defence = 0            # 防御（想办法做一个防护的感觉，比如物体表面呈现蓝色外壳）
    enhance = 1            # 加固（和之前一样的加血效果）
    change_color = 2       # 变色
    blink = 3              # 闪烁
    shake = 4              # 晃动
    bubble = 5             # 冒泡（0，1数字在头上冒）
    charge = 6          	# 充能特效

class EnumDeviceType(Enum):       # 设备类型
    empty = 0           # 空的（占位）
    core_router = 1     # 核心路由器
    router = 2          # 路由器
    switch = 3          # 交换机
    firewall = 4        # 防火墙
    wlan = 5            # wlan
    storage = 20        # 存储
    printer = 21        # 打印机
    server = 50         # 服务器
    desktop = 51        # 工作站
    laptop = 52         # 笔记本
    mobile = 53         # 移动终端

class EnumVirtualModelType(Enum):   # 虚拟空间模型
    empty = 0
    vir_att_shipgroup = 1
    vir_res_asset = 2
    vir_att_shipleader = 3
    vir_arbiter = 4
    vir_dazzle = 5

class EnumPanelType(Enum):       # 面板类型
    all_panels = 0             # 全部
    scoreboard_panel = 1       # 排行榜
    event_log_panel = 2        # 日志
    round_panel = 3            # 回合面板
    match_name_panel = 4       # 赛事名称面板
    title_panel = 5            # 题目信息面板
    team_panel = 6             # 队伍信息面板
    progress_panel = 7         # 进度条
    top_score_board = 8        # 回合排行榜  /比赛结束排行榜

class EnumCameraType(Enum):   # 镜头类型
    normal = 0      # // 固定旋转
    roaming = 1     # // 漫游
    fixed = 2       # // 静止

class EnumShowHide(Enum):
    hide = 0
    show = 1

class EnumColor(Enum):
    red = "red"
    yellow = "yellow"
    blue = "blue"

class EnumOnoff(Enum):
    off = 0
    on = 1