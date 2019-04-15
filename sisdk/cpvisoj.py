#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午7:02
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : cpvisoj.py
# @Project : cpss

import time
import sisdk.liboj.enums as oj_enums
from sisdk.cpvis import CpVis
from sisdk.consts import WORLD_TYPES, WORLD_STATES
from sisdk.liboj.scene import OjScene
from sisdk.liboj.atom_ojsysctrl import AtomOjSysctrl

class CpVisOj(CpVis):
    def __init__(self, id, title="", db_type="", db_conf="", replay=False, redis_conf={}):
        super(CpVisOj, self).__init__(WORLD_TYPES.JEOPARDY, id, title, db_type, db_conf, replay, redis_conf)
        self.oj_ui_set_title(title)
        self.scene = OjScene(self)

    # ----------------------------------------
    # oj scene/behavior messages
    # ----------------------------------------
    def oj_init_scene(self):
        """
        场景初始化，在添加完logo,题目……之后调用
        :return:
        """
        msg = self.scene.to_binary()
        return self.pub_state(WORLD_STATES.INIT_AD_SCENE, "", msg)

    def oj_update_scene(self):
        """
        在后期添加题目，logo……之后可以更新场景
        :return:
        """
        return self.oj_init_scene()

    def oj_sysctrl_sync_timing_countdown(self, seconds=0):
        """

        :param seconds: 倒计时剩余的秒数
        :return:
        """
        msg = AtomOjSysctrl.mk_oj_sync_timing(seconds)
        saved_state = {"MOMENT": time.time(), "SECONDS": seconds}
        return self.pub_state(WORLD_STATES.TIME_SECONDS_COUNTDOWN, saved_state, msg)

    def oj_add_task(self, task_id, task_name="", task_type="", score_init=0, score_current=0, solved_count=0):
        """

        :param task_id: 题目id
        :param task_name: 题目名称
        :param task_type: 题目类型
        :param score_init: 初始分数
        :param score_current: 当前分数
        :param solved_count: 解开次数
        :return:
        """
        self.scene.add_task(task_id, task_name, task_type, score_init, score_current, solved_count)

    def oj_update_task(self, task_id, task_name="", task_type="", score_init=0, score_current=0, solved_count=0):
        '''
        更新初始化之后的题目
        :param task_id: 题目id
        :param task_name: 题目名字
        :param task_type: 题目类型
        :param score_init: 初始分数
        :param score_current: 当前分数
        :param solved_count: 解开次数 0 正常显示  >1 水晶状态变化
        :return:
        '''
        self.scene.add_task(task_id, task_name, task_type, score_init, score_current, solved_count)

    def oj_add_action(self, shipgroup_id, task_id, shipgroup_name="", shipgroup_logo="", shipgroup_members = -1,
                    action=oj_enums.EnumOjActions.solve, result=False, score=0, is_first_blood=False):
        """
        shipgroup = team
        :param shipgroup_id: 队伍id
        :param task_id: 题目id
        :param shipgroup_name: 队伍名字
        :param shipgroup_logo: 队伍logo
        :param shipgroup_members: 队伍成员数量，进行一次攻击时展示出几架飞机, 默认-1 不展示飞机
        :param action: 攻击光柱的类型 scan 虚拟蓝光 solve 实质红光
        :param result:  boole 现在为True时，task上有特效
        :param score: 队伍加分 默认0
        :param is_first_blood: 是否一血 boole 是一血task变色
        :return:
        """
        self.scene.add_action(shipgroup_id, task_id, shipgroup_name, shipgroup_logo, shipgroup_members,
                              action, result, score, is_first_blood)

    # ----------------------------------------
    # ui messages
    # ----------------------------------------
    def oj_ui_set_title(self, title=""):
        """

        :param title: 表示标题的内容
        :return:
        """
        msg = AtomOjSysctrl.mk_oj_set_title(title)
        return self.pub_state(WORLD_STATES.TITLE, title, msg)

    def oj_ui_set_logo(self, logo_url=""):
        """

        :param logo_url: 右下角的产品logo
        :return:
        """
        msg = AtomOjSysctrl.mk_oj_set_logo(logo_url)
        return self.pub_state(WORLD_STATES.LOGO, logo_url, msg)

    def oj_ui_set_round(self, round_number=""):
        """
        :param round_number: 表示当前轮的数字或字符
        """
        round_number = str(round_number)
        msg = AtomOjSysctrl.mk_oj_set_round(round_number)
        return self.pub_state(WORLD_STATES.ROUND, round_number, msg)

    def oj_ui_log_message(self, message_text, message_datetime=""):
        """

        :param message_text: 发送攻击记录的信息
        :param message_datetime: 可以带上时间，选填
        :return:
        """
        if not message_datetime:
            message_datetime = time.strftime('%Y-%m-%d %X', time.localtime())
        msg = AtomOjSysctrl.mk_oj_set_message(message_text, message_datetime)
        return self.pub_message(msg)

    def oj_ui_set_bottom(self, left_message, right_message=""):
        """

        :param left_message: 中下方的左边信息
        :param right_message: 中下方右边信息，选填
        :return:
        """
        msg = AtomOjSysctrl.mk_oj_set_ui_bottom(left_message, right_message)
        value = {"left": left_message, "right": right_message}
        return self.pub_state(WORLD_STATES.BOTTOM_TEXT, value, msg)

    def restore_countdown(self, saved_state):
        message = AtomOjSysctrl.mk_oj_sync_timing(saved_state['SECONDS'])
        self.pub_state(WORLD_STATES.TIME_SECONDS_COUNTDOWN, saved_state, message)

