# -*- coding: utf-8 -*-
import logging
import time
import sisdk.libmap.enums as map_enums
from sisdk.consts import WORLD_STATES, WORLD_TYPES
from sisdk.cpvis import CpVis
from sisdk.libmap.atom_mapsysctrl import MapSysctrl
from sisdk.libmap.mapscene import MapScene, MapEntity, MapEdge
from sisdk.libmap.packaged_messages import PackagedMessages


class CpVisMap(CpVis):
    def __init__(self, id, title="", db_type="", db_conf="", replay=False, redis_conf={}):
        """

        :param id: 类的id
        :param title: 中间的标题
        :param db_type: 数据库类型 目前支持sqlite3
        :param db_conf: 数据库地址
        :param replay: 是否是回放
        :param redis_conf: redis 配置可不填
        """
        super(CpVisMap, self).__init__(WORLD_TYPES.WAR_MAP, id, title, db_type, db_conf, replay, redis_conf)
        self.map_ui_set_title(title)
        self.scene = MapScene()

        # ----------------------------------------
        # settings
        # ----------------------------------------
        # def add_entity(id, name, type, color, description, longitude, latitude):
        #     self.


    def add_entity(self, entity):
        self.scene.add_entity(entity)

    def add_edge(self, edge):
        self.scene.add_edge(edge)

    def map_load_scene(self, entity=[], edge=[], marks=[]):
        self.scene.add_load_scene(entity, edge, marks)

    def map_add_scene(self, parent_id=""):
        entities = self.scene.load_scene.get('entities')
        for entity_id, entity_obj in entities.items():
            if parent_id == entity_obj.parent_id:
                entity_obj.entity_switch = map_enums.EnumOnoff.on
                self.scene.entities[entity_id] = entity_obj
                for edge_id, edge_obj in self.scene.load_scene.get('edges').items():
                    # 筛选出与父节点所有有关连线, 过滤掉与此次创建无关的
                    if entity_obj.entity_id in edge_id.split('_') and set(edge_id.split('_')).issubset(set(self.scene.entities.keys())):
                        edge_obj.line_status = map_enums.EnumEdgeStatus.create_active
                        self.scene.edges[edge_id] = edge_obj
        marks = self.scene.load_scene.get('marks')
        for mark_name, mark in marks.items():
            self.scene.marks[mark_name] = mark
        bin_msg = self.scene.to_binary()

        if bin_msg:
            return self.pub_state(WORLD_STATES.INIT_TOPO, '', bin_msg)
        else:
            logging.error("Generating serialized topology error!")

    def map_destroy_scene(self, parent_id=""):
        entities = self.scene.load_scene.get('entities')

        for entity_id, entity_obj in entities.items():
            if parent_id == entity_obj.parent_id:
                entity_obj.entity_switch = map_enums.EnumOnoff.off
                for edge_id, edge_obj in self.scene.load_scene.get('edges').items():
                    if entity_obj.entity_id in edge_id.split('_'):
                        edge_obj.line_status = map_enums.EnumEdgeStatus.destroy
                        self.scene.edges[edge_id] = edge_obj
                        self.scene.entities[entity_id] = entity_obj

                self.map_destroy_scene(entity_id)
        bin_msg = self.scene.to_binary()

        if bin_msg:
            return self.pub_state(WORLD_STATES.INIT_TOPO, '', bin_msg)
        else:
            logging.error("Generating serialized topology error!")

    def map_show_all_scene(self, parent_id=""):
        entities = self.scene.load_scene.get('entities')

        for entity_id, entity_obj in entities.items():
            if parent_id == entity_obj.parent_id:
                entity_obj.entity_switch = map_enums.EnumOnoff.on
                self.scene.entities[entity_id] = entity_obj
                self.map_show_all_scene(entity_id)
                for edge_id, edge_obj in self.scene.load_scene.get('edges').items():
                    if entity_obj.entity_id in edge_id.split('_'):
                        edge_obj.line_status = map_enums.EnumEdgeStatus.create_active
                        self.scene.edges[edge_id] = edge_obj

        bin_msg = self.scene.to_binary()

        if bin_msg:
            return self.pub_state(WORLD_STATES.INIT_TOPO, '', bin_msg)
        else:
            logging.error("Generating serialized topology error!")

        # for entity_id, entity_obj in entities.items():
        #     self.scene.entities[entity_id] = entity_obj
        # for edge_id, edge_obj in self.scene.load_scene.get('edges').items():
        #     self.scene.edges[edge_id] = edge_obj
        #
        # bin_msg = self.scene.to_binary()
        #
        # if bin_msg:
        #     return self.pub_state(WORLD_STATES.INIT_TOPO, '', bin_msg)
        # else:
        #     logging.error("Generating serialized topology error!")

    # def map_init_scene(self, entity=[], edge=[], marks=[]):
    #     self.scene.add_entity(entity)
    #     self.scene.add_edge(edge)
    #     self.scene.add_mark(marks)
    #     bin_msg = self.scene.to_binary()
    #     if bin_msg:
    #         return self.pub_state(WORLD_STATES.INIT_TOPO, '', bin_msg)
    #     else:
    #         logging.error("Generating serialized topology error!")

    def map_init_scene_dict(self, dict_data):
        entities = []
        edges = []
        for itm in dict_data['entities']:
            obj_ent = MapEntity(**itm)
            entities.append(obj_ent)
        for itm in dict_data['edges']:
            obj_edge = MapEdge(**itm)
            edges.append(obj_edge)
        self.scene.add_load_scene(entities, edges)

        self.map_add_scene()
        # bin_msg = self.scene.to_binary()
        #
        # if bin_msg:
        #     return self.pub_state(WORLD_STATES.INIT_TOPO, '', bin_msg)
        # else:
        #     logging.error("Generating serialized topology error!")

        # ----------------------------------------
        # ad scene/behavior messages
        # ----------------------------------------

    def add_attack(self, src_obj, dest_obj, attack_type=map_enums.EnumAttackType.missile,
                   dest_type=map_enums.EnumDestType.entity, attack_speed=map_enums.EnumAttackSpeed.middile,
                   color='red', tail_width=0.5):
        """
        添加一次攻击
        :param src_obj: 攻击方id
        :param dest_obj: 目标id
        :param attack_type: 攻击的类型
        :param dest_type: 目标类型
        :param attack_speed: 攻击的速度
        :param color: 攻击的颜色
        :param tail_width: 拖尾宽度（细0.5，粗1.2，仅线条有效）
        :return:
        """
        msg = PackagedMessages.map_attack(src_obj, dest_obj, attack_type, dest_type, attack_speed, color, tail_width)

        return self.pub_message(msg)

    def add_guideline(self, src_obj, dest_obj, dest_type, description='', color='#FF0000', duration=3000):
        """
        添加引导线
        :param src_obj: 原实体id
        :param attack_type: 攻击的类型
        :param color: 引导线颜色
        :param duration: 持续时间
        :return:
        """
        msg = PackagedMessages.map_guideline(src_obj, dest_obj, dest_type, description, color, duration)

        return self.pub_message(msg)

    def add_effect(self, src_obj, effect=map_enums.EnumSandtableEffect.enhance, duration=3000, color1='', color2='',
                    icon=map_enums.EnumEffectIcon.information, switch=map_enums.EnumOnoff.on):
        """
        给一个实体添加特效
        :param src_obj: 实体的id
        :param effect: 特效类型
        :param duration: 持续时间 0 为一直存在
        :param color1: 背景色
        :param color2: 背景框的内容
        :param icon: 特效显示的图标
        :param switch: 特效的开关，可以关闭特效
        :return:
        """
        msg = PackagedMessages.map_effect(src_obj, effect, duration, color1, color2, icon, switch)

        return self.pub_message(msg)

    def add_move(self, src_obj, coordinates, move_speed=4, is_patrol=True):
        """
        移动一个实体
        :param src_obj: 实体的id
        :param coordinate1: 坐标1（元组类型）出发坐标
        :param coordinate2: 坐标2（元组类型）目的坐标
        :param move_speed: 移动速度，默认4
        :param is_patrol: 是否为巡逻模式
        :return:
        """
        msg = PackagedMessages.map_move(src_obj, coordinates, move_speed, is_patrol)
        return self.pub_message(msg)

    def add_entity_status(self, src_obj_id, switch, color):
        """
        设置实体状态
        :param src_obj_id: 实体的ID
        :param switch: 显示或隐藏旗帜 EnumOnoff On/off
        :param color: 旗帜颜色（switch ）
        :return:
        """
        msg = PackagedMessages.map_set_entity_status(src_obj_id, color, switch)
        return self.pub_message(msg)

        # ----------------------------------------
        # sysctrl messages
        # ----------------------------------------
    def set_map_settings(self, map_type, color):
        msg = MapSysctrl.mk_map_settings(map_type, color)
        return self.pub_state(WORLD_STATES.MAP_SETTINGS, '', msg)

    def map_sysctrl_sync_timing(self, astro_time=''):
        """
        设置当前时间或仿真时间
        :param astro_time: 默认为空时，只显示天文时间，传入一个时间字符串显示仿真时间
        :return:
        """
        if astro_time:
            msg = MapSysctrl.mk_sync_timing(False, astro_time=astro_time)
            return self.pub_state(WORLD_STATES.MAP_ASTRO_TIME, '', msg)
        else:
            msg = MapSysctrl.mk_sync_timing(False, astro_time=astro_time)
            return self.pub_state(WORLD_STATES.TIME_CURRENT, '', msg)

    def map_sysctrl_timing_label(self, left_timing_label, right_timing_label):
        msg = MapSysctrl.mk_set_timing_labels(left_timing_label, right_timing_label)
        return self.pub_state(WORLD_STATES.TIMING_LABEL, '', msg)
        # ----------------------------------------
        # ui messages
        # ----------------------------------------

    def map_ui_set_title(self, title=""):
        """

        :param title: 表示标题的内容
        :return:
        """
        msg = MapSysctrl.mk_set_title(title)
        return self.pub_state(WORLD_STATES.TITLE, title, msg)

    def map_ui_set_logo(self, logo_url=""):
        """

        :param logo_url: 右下角的产品logo
        :return:
        """
        msg = MapSysctrl.mk_set_logo(logo_url)
        return self.pub_state(WORLD_STATES.LOGO, logo_url, msg)

    def map_ui_toast_message(self, message_title, message_text,
                             toast_position=map_enums.EnumPosition.left,
                             toast_type=map_enums.EnumToastType.info, duration=5):
        """
        设置Toast Message系统
        :param message_title: 消息标题
        :param message_text: 消息文本
        :param toast_position:  消息位置
        :param toast_type:  消息类型（封装动作）
        :param duration:  持续时间
        """
        toast_icon = map_enums.EnumToastIcon.information
        toast_color = "green"
        if toast_type == map_enums.EnumToastType.info:
            toast_icon = map_enums.EnumToastIcon.information
            toast_color = "blue"
        elif toast_type == map_enums.EnumToastType.warning:
            toast_icon = map_enums.EnumToastIcon.exclamation
            toast_color = "orange"
        elif toast_type == map_enums.EnumToastType.exlamation:
            toast_icon = map_enums.EnumToastIcon.exclamation
            toast_color = "pink"
        elif toast_type == map_enums.EnumToastType.error:
            toast_icon = map_enums.EnumToastIcon.exclamation  # TODO:加一个error图标
            toast_color = "red"
        elif toast_type == map_enums.EnumToastType.question:
            toast_icon = map_enums.EnumToastIcon.question
            toast_color = "yellow"

        msg = MapSysctrl.mk_ui_toast(position=toast_position,
                                     icon=toast_icon,
                                     text_title=message_title,
                                     text_content=message_text,
                                     switch=map_enums.EnumOnoff.on,
                                     duration=duration,
                                     color=toast_color)
        return self.pub_message(msg)

    def map_ui_log_message(self, message_text, message_datetime=""):
        """
        显示在右下角的攻击记录
        :param message_text: 攻击记录的内容
        :param message_datetime: 发生的时间 选填
        :return:
        """
        if not message_datetime:
            message_datetime = time.strftime('%Y-%m-%d %X', time.localtime())
        msg = MapSysctrl.mk_ui_set_message(message_text, message_datetime)
        return self.pub_message(msg)

    def sysctrl_focus(self, obj_id, duration):
        """
        镜头的一个聚焦效果
        :param obj_id: 聚焦的建筑
        :param duration: 持续时间毫秒
        :return:
        """
        msg = MapSysctrl.mk_focus(
            obj_id=obj_id,
            duration=duration,
        )
        return self.pub_message(msg)

    def restore_current(self):
        msg = MapSysctrl.mk_sync_timing(False)
        return self.pub_state(WORLD_STATES.TIME_CURRENT, '', msg)
