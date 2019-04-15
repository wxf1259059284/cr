#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-15 上午11:19
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : enums.py
# @Project : cpss

#from ..consts import Enum
Enum = object

class EnumCameraType(Enum):   # 镜头类型
    normal = 0      # // 固定旋转
    roaming = 1     # // 漫游
    fixed = 2       # // 静止

class EnumPanelType(Enum): #// 面板类型
    all = 0    #// 全部
    scoreboard = 1    #// 排行
    event_log = 2     #// 日志
    netflow = 3

class EnumChartType(Enum):  #图表类型
    bar = 0
    pie = 1

class EnumPanelAction(Enum):
    hide = 0
    show = 1

class EnumShowHide(Enum):
    hide = 0
    show = 1

class EnumPosition(Enum):
    left = 0
    top = 1
    center = 2

class EnumToastType(Enum):
    info = 0
    warning = 1
    exlamation = 2
    question = 3
    error = 4

class EnumToastIcon(Enum):    # //图标（可以显示在头顶上，或围绕转圈）
    no_icon = 0         # //无
    exclamation = 1     # //惊叹号
    information = 2     # //信息
    question = 3        # //问题

class EnumOnoff(Enum):
    off = 0
    on = 1

class EnumOrientation(Enum):     #//排布方式
    automatic = 0          #//根节点
    horizontal = 1         #//横向
    vertical = 2           #//纵向

class EnumEntityType(Enum):   #//网络实体类型
    abstract = 0         #//预留虚拟模型
    subnet = 1          #//子网
    device = 2          #//设备

class EnumEffectIcon(Enum):   #//图标（可以显示在头顶上，或围绕转圈）
    no_icon = 0         #//无
    exclamation = 1     #//惊叹号
    information = 2     #//信息
    question = 3        #//问题
    wrench = 4          #//扳手
    cog = 5             #//齿轮（工作状态，两个齿轮动态咬合叠加转动）


class EnumAttackSpeed(Enum):  # //攻击速度
    slow = 0  # // 慢
    middile = 1  # // 中
    fast = 2  # // 快


class EnumDestType(Enum):
    entity = 0     # // 目标为实体
    edge = 1       # // 目标为链路


class EnumAttackType(Enum):
    missile = 0   # // 导弹
    line = 1      # // 线条


# class EnumAttackIntensity(Enum):     #//攻击强度
#     attack_weak = 0            #//弱
#     attack_moderate = 1        #//中等
#     attack_heavy = 2           #//重
#     attack_extreme = 3         #//极重
#     attack_epic = 4            #//最重

class EnumSandtableEffect(Enum):      # //特效类型(可以在单个物体上展示的特效)
    defence = 0        # // 防御（想办法做一个防护的感觉，比如物体表面呈现蓝色外壳）
    enhance = 1        # // 加固（和之前一样的加血效果）
    change_color = 2   # // 变色
    smoke = 3          # // 冒烟特效
    war_fog = 4        # // 战争迷雾 （暂无）
    radar_anim = 5     # // 雷达
    icon = 6           # // 图标
    namepanel_color = 7  # // 名称面板背景色(需要配合参数：Color1背景色，如black;Color2文本内容，如 < color = white > UnitName < / color >)

class EnumHtmlPanelAction(Enum):
    show = 0            #显示
    hide = 1            #隐藏
    reload = 2          #刷新
    close = 3           #销毁

class EnumProgressAction(Enum):
    pause = 0   # 暂停
    play = 1    # 播放
    speed = 2   # 倍速

class EnumTrend(Enum):
    still = 0
    up = 1
    down = 2

class EnumModelType(Enum):
    warplane = 0   # //战斗机
    drone = 1      # //无人机
    satellite = 2  # 卫星
    radar = 3  # // 雷达
    submarine = 4  # // 潜水艇
    destroyer = 5  # // 驱逐舰
    aircraft_carrier = 6  # // 航母

    command_center = 7  # // 指挥中心
    command_post = 8  # // 指挥所
    communications_tower = 9  # // 通信塔台
    reef = 10  # // 岛礁
    power_station = 11     # // 电站
    placeholder = 12       # // 电线杆放置的空点


class EnumStatus(Enum):     # //状态
    normal = 0       # //正常
    downtime = 1       # //宕机

class EnumEdgeStatus(Enum):
    create_active = 0    # // 创建且激活链路
    create_inactive = 1  # // 创建且未激活链路
    destroy = 2          # // 销毁链路

class EnumLineType(Enum):
    waves = 0       # // 3D电波
    cable = 1       # // 有线电缆
    icon_line = 2   # // 发射图标
    electric_pole = 3  # // 电线电缆


class EnumIconType(Enum):
    wave = 0       # // 电波图标
    heartbeat = 1  # // 心跳图标
    sin = 2        # // 正弦波图标
    wifi = 4       # // WIFI图标
    audio = 5      # // Audio图标
    battle = 6     # // 指控图标
    text = 7       # // 文本图标
    data = 8       # // 数据图标


class EnumMapType(Enum):
    naturalAlt1 = 0    # // color为水的颜色
    naturalAlt2 = 1    # // color为水的颜色
    AltStyleGrey = 2   # // 固定色深灰调
    AltStyleBrown = 3  # // 固定色宗调
    AltStyleGreen = 4  # // 固定色绿色
    SolidColor = 5     # // color为全地图颜色


class EnumMapMark(Enum):
    province = 0  # // 省
    city = 1      # // 市
    country = 2   # // 县，镇，村


class EnumOnoff(Enum):
    off = 0
    on = 1

if __name__ == "__main__":
    EnumHtmlPanelAction.parse_string("close")