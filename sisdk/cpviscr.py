#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-21 下午1:30
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : cpviscr.py.py
# @Project : cpss

import time
import logging
from sisdk.cpvis import CpVis
from sisdk.consts import WORLD_TYPES, WORLD_STATES
from sisdk.libcr.topo_generator import XojScene, MultiXojScene
from sisdk.messages import wrap_message
from sisdk.libcr.packaged_messages import PackagedMessages
from sisdk.libcr.atom_sysctrl import AtomSysctrl
from sisdk.libcr.atom_ui import AtomUi
import sisdk.libcr.enums as Enums


class CpVisCr(CpVis):
    def __init__(self, id, title="", db_type="", db_conf="", replay=False, redis_conf={}):
        super(CpVisCr, self).__init__(WORLD_TYPES.CYBER_RANGE, id, title, db_type, db_conf, replay, redis_conf)
        self.cr_ui_set_title(title)
        self.html_panels = []
        self.chart_panels = {}
        self.topology = XojScene()

    # ----------------------------------------
    # topology messages
    # ----------------------------------------
    def cr_topology_init_scene(self, topo_data, root_entity, auto_arrange_root=True):
        """
        初始化拓扑地图
        :param topo_data: oj中的json网络描述
        :param root_entity: 定义一个根节点，展开topo
        :param auto_arrange_root:
        :return:
        """
        self.topology.from_json(topo_data)
        self.topology.make_tree(root_entity, auto_arrange_root)
        bin_msg = self.topology.to_binary()
        if bin_msg:
            message = wrap_message(bin_msg)
            logging.info(self.topology.to_json())
            return self.pub_state(WORLD_STATES.INIT_TOPO, topo_data, message)
        else:
            logging.error("Generating serialized topology error!")

    def cr_topology_init_multi_scene(self, topo_data_list, root_name):
        multi_scene = MultiXojScene(root_name)
        for topo in topo_data_list:
            logging.info("Generating ", topo[1])
            multi_scene.add_subnet(topo[0], topo[1])
        bin_msg = multi_scene.to_binary()
        if bin_msg:
            message = wrap_message(bin_msg)
            logging.info(multi_scene.to_json())
            return self.pub_state(WORLD_STATES.INIT_TOPO, topo_data_list, message)
        else:
            logging.error("Generating serialized multiple topology error!")

    def cr_topology_act_attack(self, src_obj, dest_obj, success=True, show_guildline=True,
                               show_panel=False, panel_text="", panel_os="",
                               change_color=False, show_top_icon=False):
        """
        进行一次拓扑攻击
        :param src_obj: 发起攻击的对象
        :param dest_obj: 被攻击的对象
        :param success: boole 默认true 红色 false 蓝色
        :param show_guildline: boole 默认true 显示上边的线 false 不显示
        :param show_panel: boole 默认false 不显示 true dest_obj上边显示panel_text，panel_os 所填信息
        :param panel_text: 所显示的信息
        :param panel_os: 所在位置
        :param change_color: boole 默认false 不变色 true dest_obj 变色
        :param show_top_icon: boole 默认false
        :return:
        """
        msg = PackagedMessages.topo_attack(src_obj, dest_obj, success, show_guildline,
                                           show_panel, panel_text, panel_os,
                                           change_color, show_top_icon)
        return self.pub_message(msg)

    def cr_topology_act_guideline(self, src_obj, dest_obj, color='00CCFF', duration=5):
        """
        发出一道射线
        :param src_obj: 发起攻击的对象
        :param dest_obj: 被攻击的对象
        :param color: 默认蓝色，可填充去掉# 的十六进制颜色
        :param duration: 默认 5s 特效持续时间 int 单位 s
        :return:
        """
        msg = PackagedMessages.topo_guideline(src_obj, dest_obj, color, duration)
        return self.pub_message(msg)

    def cr_topology_act_effect(self, obj, effect=Enums.EnumTopologyEffect.enhance, color1='', color2=''):
        """
        给一个对象加特效
        :param obj: 指定一个对象
        :param effect: 给该对象的效果
        :return:
        """
        msg = PackagedMessages.topo_effect(obj, effect, color1, color2)
        return self.pub_message(msg)

    def cr_topology_show_entity_panel(self, obj, os_name, panel_text):
        """
        拓扑场景的展示板
        :param obj:
        :param os_name:
        :param panel_text:
        :return:
        """
        msg = PackagedMessages.topo_show_entity_panel(obj, os_name, panel_text)
        return self.pub_message(msg)

    def cr_topology_show_entity_icon(self, obj, icon=Enums.EnumEffectIcon.exclamation, color=''):
        """
        展示头像
        :param obj: 指定的对象
        :param icon: 头像的样式，在枚举里找
        :param color: 显示的颜色 可填充去掉# 的十六进制颜色
        :return:
        """
        msg = PackagedMessages.topo_show_entity_icon(obj, icon, color)
        return self.pub_message(msg)

    # ----------------------------------------
    # sandtable messages
    # ----------------------------------------
    def cr_sandtable_act_attack(self, src_obj, dest_obj, success=True, show_guildline=True,
                                icon=Enums.EnumEffectIcon.information,
                                change_indicators=False, percentage_inner=0, percentage_outer=0, top_text=""):
        """
        沙盘场景的一次攻击
        :param src_obj: 发起攻击的对象
        :param dest_obj: 被攻击的对象
        :param success: boole 默认true 红色 false 蓝色
        :param show_guildline: boole 默认true 显示上边的线 false 不显示
        :param icon: 圈内下边的小图标
        :param change_indicators: boole 默认false 不切换圆圈里内容
        :param percentage_inner: 内圈的百分比 0-1 的浮点数
        :param percentage_outer: 外圈的百分比 0-1 的浮点数
        :param top_text: 圆圈里的替换内容
        :return:
        """
        msg = PackagedMessages.sandtable_attack(src_obj, dest_obj, success, show_guildline, icon,
                                                change_indicators, percentage_inner, percentage_outer, top_text)
        return self.pub_message(msg)

    def cr_sandtable_act_guideline(self, src_obj, dest_obj, color='00CCFF', duration=5):
        """
        沙盘发起一道射线
        :param src_obj: 发起攻击的对象
        :param dest_obj: 被攻击的对象
        :param color: 线的颜色 默认蓝
        :param duration: 持续时间 5s

        :return:
        """
        msg = PackagedMessages.sandtable_guideline(src_obj, dest_obj, color, duration)
        return self.pub_message(msg)

    def cr_sandtable_act_effect(self, obj, effect=Enums.EnumSandtableEffect.charge, duration=10, color1='', color2=''):
        """
        沙盘某个对象的特效
        :param obj: 目标对像
        :param effect: 效果，请去枚举中找支持的效果
        :param duration: 持续时间 s
        :param color1: 选填 某些特效需要用到
        :param color2: 选填 某些特效需要用到
        :return:
        """
        msg = PackagedMessages.sandtable_effect(obj, effect, duration, color1, color2)
        return self.pub_message(msg)

    def cr_sandtable_update_panel(self, obj, percentage_inner, percentage_outer, top_text, icon=Enums.EnumEffectIcon.no_icon):
        """
        更新沙盘的仪表板
        :param obj: 更新的对象
        :param percentage_inner: 内圈的百分比 0-1 的浮点数
        :param percentage_outer: 外圈的百分比 0-1 的浮点数
        :param top_text: 圆圈里的替换内容
        :param icon: 默认无图标  更新下边显示的图标
        :return:
        """
        msg = PackagedMessages.sandtable_updta_top_icon(obj, icon, top_text, percentage_inner, percentage_outer)
        return self.pub_message(msg)

    # ----------------------------------------
    # sysctrl messages
    # ----------------------------------------
    def cr_sysctrl_toggle_camera(self, camera_type=Enums.EnumCameraType.normal):
        msg = AtomSysctrl.mk_toggle_camera(camera_type)
        return self.pub_message(msg)

    def cr_sysctrl_toggle_scene(self, scenario_type=Enums.EnumScenarioType.topology):
        """
        切换场景
        :param scenario_type: Enums.EnumScenarioType.topology 沙盘/拓扑两个场景
        :return:
        """
        msg = AtomSysctrl.mk_toggle_scene(scenario_type)
        return self.pub_message(msg)

    def cr_sysctrl_sync_timing_countdown(self, countdown_seconds=0):
        """
        存入倒计时
        :param countdown_seconds: int 型，倒计时剩余秒数
        :return:
        """
        msg = AtomSysctrl.mk_sync_timing(True, countdown_seconds * 1000)
        saved_state = {"MOMENT": time.time(), "SECONDS": countdown_seconds}
        return self.pub_state(WORLD_STATES.TIME_SECONDS_COUNTDOWN, saved_state, msg)

    def cr_sysctrl_sync_timing(self):
        msg = AtomSysctrl.mk_sync_timing(False)
        return self.pub_state(WORLD_STATES.TIME_CURRENT, '', msg)

    def cr_sysctrl_focus_entities(self, id1, id2="", id3=""):
        """
        聚焦设备
        :param id1: 设备编号
        :param id2:
        :param id3:
        :return:
        """
        msg = AtomSysctrl.mk_focus(obj_id1=id1, obj_id2=id2, obj_id3=id3, duration=10)
        return self.pub_message(msg)

    def cr_sysctrl_focus_subnet(self, subnet_id):
        """
        聚焦网络
        :param subnet_id: 网络编号
        :return:
        """
        msg = AtomSysctrl.mk_focus_subnet(subnet_id=subnet_id, duration=10)
        return self.pub_message(msg)

    # ----------------------------------------
    # ui messages
    # ----------------------------------------
    def cr_ui_set_title(self, title=""):
        """
        设置顶部标题文本
        :param title: 标题文本
        """
        # if not type(title) in [str, unicode]:
        #     raise TypeError("argument 'title' must be str or unicode type.")
        msg = AtomUi.mk_ui_set_title(str(title))
        return self.pub_state(WORLD_STATES.TITLE, title, msg)

    def cr_ui_set_logo(self, logo_url=""):
        """
        设置顶部标题的LOGO图片URL
        :param logo_url:
        """
        # if not type(logo_url) is str or :
        #     raise exceptions.TypeError("argument 'logo' must be str or unicode type.")
        if not logo_url.startswith("http"):
            raise ValueError("value 'logo_url' must starts with http/https.")
        msg = AtomUi.mk_ui_set_logo(logo_url)
        self.save_state(WORLD_STATES.LOGO, logo_url)
        return self.pub_state(WORLD_STATES.LOGO, logo_url, msg)

    def cr_ui_toast_message(self, message_title, message_text,
                            toast_position=Enums.EnumPosition.left,
                            toast_type=Enums.EnumToastType.info, duration=5):
        """
        设置Toast Message系统
        :param message_title: 消息标题
        :param message_text: 消息文本
        :param toast_position:  消息位置
        :param toast_type:  消息类型（封装动作）
        """
        toast_icon = Enums.EnumToastIcon.information
        toast_color = "green"
        if toast_type == Enums.EnumToastType.info:
            toast_icon = Enums.EnumToastIcon.information
            toast_color = "blue"
        elif toast_type == Enums.EnumToastType.warning:
            toast_icon = Enums.EnumToastIcon.exclamation
            toast_color = "orange"
        elif toast_type == Enums.EnumToastType.exlamation:
            toast_icon = Enums.EnumToastIcon.exclamation
            toast_color = "pink"
        elif toast_type == Enums.EnumToastType.error:
            toast_icon = Enums.EnumToastIcon.exclamation  # TODO:加一个error图标
            toast_color = "red"
        elif toast_type == Enums.EnumToastType.question:
            toast_icon = Enums.EnumToastIcon.question
            toast_color = "yellow"

        msg = AtomUi.mk_ui_toast(position=toast_position,
                                 icon=toast_icon,
                                 text_title=message_title,
                                 text_content=message_text,
                                 switch=Enums.EnumOnoff.on,
                                 duration=duration,
                                 color=toast_color)
        return self.pub_message(msg)

    def cr_ui_log_message(self, message_text, message_datetime=""):
        """
        显示在右下角的攻击记录
        :param message_text: 攻击记录的内容
        :param message_datetime: 发生的时间 选填
        :return:
        """
        if not message_datetime:
            message_datetime = time.strftime('%Y-%m-%d %X', time.localtime())
        msg = AtomUi.mk_ui_set_message(message_text, message_datetime)
        return self.pub_message(msg)

    def cr_ui_html_panel_show(self, url, title="", closable=False, width=640, height=480, pos_x=400, pos_y=300):
        if url not in self.html_panels:
            msg = AtomUi.mk_ui_html_panel_show(url, url, title, width, height, closable, pos_x, pos_y)
            self.html_panels.append(url)
            return self.pub_message(msg)

    def cr_ui_html_panel_close(self, url):
        if url in self.html_panels:
            msg = AtomUi.mk_ui_html_panel_close(url)
            self.html_panels.remove(url)
            return self.pub_message(msg)

    def cr_ui_html_panel_refresh(self, url):
        if url in self.html_panels:
            msg = AtomUi.mk_ui_html_panel_reload(url)
            return self.pub_message(msg)

    def cr_ui_chart_panel_show(self, chart_obj, closable=False, width=640, height=480, pos_x=400,
                               pos_y=300):
        """
        展示图表
        :param chart_obj: 实例化的对象
        :param closable: boole
        :param width: 图表的宽
        :param height: 图标的高
        :param pos_x: 以屏幕左上角为坐系的x轴
        :param pos_y: 以屏幕左上角为坐系的y轴
        :return:
        """
        panel_id = "CHART_" + str(chart_obj.chart_id)
        title = chart_obj.title
        if panel_id not in self.html_panels:
            # 先创建一个htmlPanel
            url = chart_obj.html_file
            msg = AtomUi.mk_ui_html_panel_show(panel_id, url, title, width, height, closable, pos_x, pos_y)
            self.html_panels.append(panel_id)
            # 用state显示图表
            self.pub_state(panel_id, "", msg)
            time.sleep(1)
            init_data = chart_obj.to_json()
            msg = AtomUi.mk_ui_chart_init(panel_id, init_data)
            self.chart_panels[chart_obj.chart_id] = chart_obj
            return self.pub_state(WORLD_STATES.CHART_INIT, {"panel_id": panel_id, "init_data": init_data}, msg)

    def cr_ui_chart_panel_update(self, chart_id):
        """
        更新图表
        :param chart_id: 展示图表的名字
        :return:
        """
        panel_id = "CHART_" + str(chart_id)
        if chart_id in self.chart_panels:
            data = self.chart_panels[chart_id].to_json()
            msg = AtomUi.mk_ui_chart_init(panel_id, data)
            return self.pub_message(msg)

    def cr_ui_chart_panel_close(self, chart_id):
        panel_id = "CHART_" + str(chart_id)
        msg = AtomUi.mk_ui_html_panel_close(panel_id)
        try:
            self.chart_panels.pop(chart_id)
        except Exception:
            logging.warning("Chart with id %s not exists." % chart_id)
        return self.pub_message(msg)

    def restore_countdown(self, saved_state):
        message = AtomSysctrl.mk_sync_timing(True, saved_state['SECONDS'] * 1000)
        self.pub_state(WORLD_STATES.TIME_SECONDS_COUNTDOWN, saved_state, message)

    def restore_current(self):
        msg = AtomSysctrl.mk_sync_timing(False)
        return self.pub_state(WORLD_STATES.TIME_CURRENT, '', msg)
