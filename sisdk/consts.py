#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-21 上午10:05
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : consts.py.py
# @Project : cpss

import os

class Enum(object):
    @classmethod
    def parse_string(cls, property_string):
        for prop in cls.__dict__:
            if prop == property_string:
                return cls.__getattribute__(cls, prop)
        return None

    @classmethod
    def value_to_name(cls, val):
        for prop in cls.__dict__:
            if cls.__getattribute__(cls, prop) == val:
                return prop
        return None

    @classmethod
    def to_list(cls):
        out = [cls.__getattribute__(cls, prop) for prop in cls.__dict__]
        return out

class CONST:
    REDIS_DB_MQ = 5
    REDIS_DB_STORE = 3

    VIS_CLIENT_CONNECTED = "VIS_CLIENT_CONNECTED"
    VIS_CLIENT_CLOSED = "VIS_CLIENT_CLOSED"

    REQUEST_CHANNEL = "REQUEST_CHANNEL"

class WORLD_TYPES:
    JEOPARDY = 1
    ATTACK_DEFENSE = 2
    CYBER_RANGE = 3
    WAR_MAP = 4

WORLD_TYPE_REVERSE = {1:"OJ", 2:"AD", 3:"CR", 4:'MAP'}

class EnumRequestType(Enum):
    focus_click_unit = 0       #聚焦设备请求
    focus_click_subnet = 1     #聚焦网络请求
    progress_click = 2        #进度请求
    progress_click_play = 3      #播放请求
    progress_click_pause = 4      #暂停请求
    progress_click_speed = 5     #播放

    click_show_next_subnet = 6  # // 显示下一级子网
    click_show_all_subnets = 7  # // 显示全部子网
    click_hide_all_subnets = 8  # // 取消显示子网




class PARAMS:
    APP_ROOT = os.path.dirname(os.path.join(os.path.dirname(__file__)))
    APP_CONFIG_FILE = APP_ROOT + os.sep + "conf.ini"


class OJ_ACTIONS:
    FIRST_BLOOD = 1
    SECOND_BLOOD = 2
    THIRD_BLOOD = 3
    SOLVED_NO_BLOOD = 9
    UNSOLVED = 20
    EXPLORING = 50
    AI_EXPLORING = 51

class MESSAGE_TEMPLATES:
     EXPLORING = "%s <color=%s>%s</color> is Exploring <color=%s>%s</color>!"
     SOLVED = "%s <color=%s>%s</color> <color=%s>Solved</color> <color=%s>%s</color>!"
     UNSOLVED = "%s <color=%s>%s</color> Attempted on <color=%s>%s</color>!"
     ATTACK_ACCESS = "%s <color=%s>%s</color> launched <color=%s>%s</color> on <color=%s>%s</color>"
     NORMAL_ACCESS = "%s <color=%s>%s</color> accessed <color=%s>%s</color>"

class PRESET_COLORS(Enum):
    red = "red"
    cyan = "cyan"
    blue = "blue"
    darkblue = "darkblue"
    lightblue = "lightblue"
    purple = "purple"
    yellow = "yellow"
    lime = "lime"
    fuchsia = "fuchsia"
    white = "white"
    silver = "silver"
    grey = "grey"
    black = "black"
    orange = "orange"
    brown = "brown"
    maroon = "maroon"
    green = "green"
    olive = "olive"
    navy = "navy"
    teal = "teal"
    aqua = "aqua"
    magenta = "magenta"

#class MESSAGE_TEMPLATES:
#    EXPLORING = u"%s <color=%s>%s</color> 开始解题 <color=%s>%s</color>!"
#    SOLVED = u"%s <color=%s>%s</color> <color=%s>解出了</color> <color=%s>%s</color>!"
#    UNSOLVED = u"%s <color=%s>%s</color> 正在尝试 <color=%s>%s</color>!"

class CONTEST_TYPE:
    CONTEST_TYPE_CG = 0  # 组队闯关型
    CONTEST_TYPE_NCG = 1  # 组队解题型
    CONTEST_TYPE_SHARE = 2  # 组队分享型
    CONTEST_TYPE_NCG_PERSON = 3  # 个人解题型
    CONTEST_TYPE_CG_PERSON = 4  # 个人闯关型
    CONTEST_TYPE_CG_FINAL = 5  # 总决赛
    CONTEST_TYPE_CG_WITHPAPER = 6 #带试卷的比赛
    CONTEST_TYPE_TEAM_LEVEL = 7   #组队分层

class EVENT_MODE:   #used in ad3 ctf mode
    MODE_INDIVIDUAL = 1
    MODE_TEAM = 2

class EVENT_TYPE:
    TYPE_JEOPARDY = 2
    TYPE_AandD = 5

class WORLD_STATES:
    """
    命名规范：一定注意，1、所有INIT_开头的状态，不会在点击进度条时重新发给客户端；2、变量名和字符串一定要保持一致
    """
    TITLE = "TITLE"
    LOGO = "LOGO"
    INIT_TOPO = "INIT_TOPO"
    SCOREBOARD = "SCORE_BOARD"
    TIME_SECONDS_COUNTDOWN = "TIME_SECONDS_COUNTDOWN"
    TIME_CURRENT = "TIME_CURRENT"
    # CR
    CHART_INIT = "CHART_INIT"
    # AD
    ROUND = "ROUND"
    BOTTOM_TEXT = "BOTTOM_TEXT"
    INIT_AD_SCENE = "INIT_AD_SCENE"
    INIT_OJ_SCENE = "INIT_OJ_SCENE"
    # MAP
    MOVE = "MOVE"
    MAP_MARK = "MAP_MARK"
    MAP_ASTRO_TIME = "MAP_ASTRO_TIME"
    TIMING_LABEL = 'TIMING_LABEL'
    MAP_SETTINGS = 'MAP_SETTINGS'


TASK_TYPE_TABLE_MAP = {1:("practice_real_vuln_realvulntask","practice_real_vuln_category"),
                       2:("practice_exercise_practiceexercisetask","practice_exercise_category"),
                       4:("practice_attack_defense_practiceattackdefensetask","practice_attack_defense_category")}

COLOR ={"pink": "#6a1b9a",
        "red": "#b71b1c",
        "orange": "#ff8e01",
        "yellow": "#fed835",
        "purple": "#842dce",
        "green": "#4cb050",
        "blue": "#4cb050",
        "cyan": "#3b9c9c",
        "magenta": "#ff00ff"}

STATISTICS = {"system_start_time": "",
              "data_sent": 0,   #sent data (bytes)
              "clients_connected": 0    #connected websocket clients
              }

TEAM_ID_OFFSET = {
    'NORMAL': 0,
    'AI': 10000,
    'Personal': 0
}

TEAM_IP_MAP = {
    ""
}

ACCESS_TYPE = {
    0: "Normal",
    1: "PHP Hacking",
    2: "SQL Injection"
}

