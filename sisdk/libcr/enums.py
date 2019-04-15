#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @date: 2018/5/29 23:00
# @author：Ivan Wang

from ..consts import Enum

class EnumMessageType(Enum):
    behavior = 0    # 行为
    command = 1     # 指令
    request = 2     # 客户端指令

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

class EnumScenarioType(Enum):
    all_scenarios = 0
    sandtable = 1  # 沙盘场景
    topology = 2

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

class EnumDeviceType(Enum):       #//设备类型
    empty = 0               #//空的（占位）
    core_router = 1         #//核心路由器
    router = 2              #//路由器
    switch = 3              #//交换机
    firewall = 4            #//防火墙
    wlan = 5                #//wlan
    storage = 20            #//存储
    printer = 21            #//打印机
    server = 50             #//服务器
    desktop = 51            #//工作站
    laptop = 52             #//笔记本
    mobile = 53             #//移动终端

class EnumEffectIcon(Enum):   #//图标（可以显示在头顶上，或围绕转圈）
    no_icon = 0         #//无
    exclamation = 1     #//惊叹号
    information = 2     #//信息
    question = 3        #//问题
    wrench = 4          #//扳手
    cog = 5             #//齿轮

class EnumAttackIntensity(Enum):     #//攻击强度
    attack_weak = 0            #//弱
    attack_moderate = 1        #//中等
    attack_heavy = 2           #//重
    attack_extreme = 3         #//极重
    attack_epic = 4            #//最重

class EnumSandtableEffect(Enum):      #//特效类型(可以在单个物体上展示的特效)
    defence = 0               #//防御
    enhance = 1               #//加固
    change_color = 3          #//变色  需要传入颜色值1种
    blink = 4                 #//闪烁  需要传入颜色值1/2种
    charge = 5                # 充电

class EnumTopologyEffect(Enum):            #特效类型(可以在单个物体上展示的特效)
    defence = 0                #防御（想办法做一个防护的感觉，比如物体表面呈现蓝色外壳）
    enhance = 1                #加固（和之前一样的加血效果）
    change_color = 3           #变色  需要传入颜色值
    blink = 4              #闪烁   需要传入颜色值
    shake = 5              #晃动
    bubble = 6                 # 冒泡（0，1数字在头上冒）
    icon_indicator = 7             # 头顶上的小图标
    icon_whirl = 8                 # 围绕转圈的小图标
    charge = 9                     # 蓝色的泡泡绕着建筑向外冒
    change_backgroud_color = 10    # 改变背景颜色     需要传入颜色值
    blink_background = 11          # 背景闪烁       需要传入颜色值

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


if __name__ == "__main__":
    EnumHtmlPanelAction.parse_string("close")