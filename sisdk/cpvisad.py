#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午7:02
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : cpvisad.py
# @Project : cpss

import time
import sisdk.libad.enums as ad_enums
from sisdk.cpvis import CpVis
from sisdk.consts import WORLD_TYPES, WORLD_STATES
from sisdk.libad.scene import AdScene
from sisdk.libad.atom_adsysctrl import AtomAdSysctrl
from sisdk.libad.atom_adbehavior import AtomAdBehavior
from sisdk.libad.packaged_messages import PackagedMessages


class CpVisAd(CpVis):
    def __init__(self, id, title="", db_type="", db_conf="", replay=False, redis_conf={}):
        super(CpVisAd, self).__init__(WORLD_TYPES.ATTACK_DEFENSE, id, title, db_type, db_conf, replay, redis_conf)
        self.ad_ui_set_title(title)
        self.scene = AdScene()

    # ----------------------------------------
    # settings
    # ----------------------------------------
    def add_team(self, id, name, logo="", init_score=0, color=""):
        """

        :param id: 队伍id
        :param name: 队伍名字
        :param logo: 队伍logo
        :param init_score: 初始分数
        :param color: 队伍初始的颜色
        :return:
        """
        self.scene.add_team(team_id=id, team_name=name, team_logo=logo, init_score=init_score, team_color=color)

    def add_task(self, id, name=""):
        """

        :param id: 题目id
        :param name: 题目名字
        :return:
        """
        self.scene.add_task(task_id=id, task_name=name)

    def add_puzzle(self, id, name="", score=0, solved=0):
        """

        :param id: 水晶id
        :param name: 水晶名字
        :param score: 水晶的分数
        :param solved:            # 0 正常状态，尝试1,2,3都变绿，未发现1,2,3有不同
        :return:
        """
        self.scene.add_puzzle(puzzle_id=id, puzzle_name=name, puzzle_score=score, puzzle_solved=solved)


    # ----------------------------------------
    # ad scene/behavior messages
    # ----------------------------------------
    def ad_init_scene(self):
        """
        场景初始化，在添加完logo,队伍，题目，水晶……之后调用
        TODO：实现横排、竖排
        """
        msg = self.scene.to_binary()
        return self.pub_state(WORLD_STATES.INIT_AD_SCENE,"",msg)

    def ad_attack(self, src_team_id, dest_team_id, dest_task_id,
                  intensity=ad_enums.EnumAttackIntensity.attack_moderate,
                  success=False, firstblood=False, src_gain_score=0, dest_lose_score=0, color="red"):
        """

        :param src_team_id: 攻击队伍id
        :param dest_team_id: 被攻击方id
        :param dest_task_id: 被攻击方题目id
        :param intensity: 攻击强度
        :param success: 是否攻击成功 boole  # 未成功有护罩
        :param firstblood: 是否一血 boole  # 现在一血的特效是光柱粗大
        :param src_gain_score: 攻方得分 默认0 选填
        :param dest_lose_score: 防守方失分 默认0 选填
        :param color: 颜色 默认红  # 激光的颜色貌似没有变化
        :return:
        """
        msg = PackagedMessages.attack(src_team_id=src_team_id,
                                      dest_team_id=dest_team_id,
                                      dest_unit_id=dest_task_id,
                                      intensity=intensity,
                                      success=success,
                                      firstblood=firstblood,
                                      src_score=src_gain_score,
                                      dest_score=dest_lose_score,
                                      color=color)
        return self.pub_message(msg)

    def ad_puzzle_attack(self, src_team_id, dest_puzzle_id,
                         success=False, firstblood=False, gain_score=0):
        """

        :param src_team_id: 攻击队伍id
        :param dest_puzzle_id: 目标水晶id
        :param success: 是否攻击成功 boole
        :param firstblood: 是否一血 boole
        :param gain_score: 攻方得分
        :return:
        """
        msg = PackagedMessages.puzzle_attack(src_team_id=src_team_id,
                                             dest_puzzle_id=dest_puzzle_id,
                                             success=success,
                                             firstblood=firstblood,
                                             src_score=gain_score)
        return self.pub_message(msg)

    def ad_arbiter_attack(self, dest_team_id, dest_task_id,
                          attack_intensity=ad_enums.EnumAttackIntensity.attack_moderate,
                          dest_score=0):
        """

        :param dest_team_id: 目标队伍id
        :param dest_task_id: 目标队伍题目id
        :param attack_intensity: 攻击的强度
        :param dest_score:  目标分数
        :return:
        """
        msg = PackagedMessages.arbiter_attack(dest_team_id=dest_team_id,
                                              dest_unit_id=dest_task_id,
                                              attack_intensity=attack_intensity,
                                              dest_score = dest_score)
        return self.pub_message(msg)

    def ad_task_enhance(self, team_id, task_id, duration=10):
        """
        加固特效，会有一直加血状态
        :param team_id: 队伍id
        :param task_id: 题目id
        :param duration: 持续时间  # 更改未发现变化
        :return:
        """
        dest_unit_id = "unit-%s-%s" % (str(team_id), str(task_id))
        msg = AtomAdBehavior.mk_ad_effect(team_id=team_id,
                                          team_child_id=dest_unit_id,
                                          switch=ad_enums.EnumOnoff.on,
                                          effect=ad_enums.EnumAdEffect.enhance,
                                          duration=duration)
        return self.pub_message(msg)

    # ----------------------------------------
    # sysctrl messages
    # ----------------------------------------
    def ad_sysctrl_toggle_scene(self, scenario_type=ad_enums.EnumScenarioType.virtual_starwar):
        """

        :param scenario_type: 场景切换，目前ad有太空和机房两个场景
        :return:
        """
        msg = AtomAdSysctrl.mk_ad_toggle_scene(scenario_type)
        return self.pub_message(msg)

    def ad_sysctrl_sync_timing_countdown(self, countdown_seconds=0):
        """

        :param countdown_seconds: 存储倒计时单位s
        :return:
        """
        msg = AtomAdSysctrl.mk_ad_sync_timing(countdown_seconds)
        saved_state = {"MOMENT": time.time(), "SECONDS": countdown_seconds}
        return self.pub_state(WORLD_STATES.TIME_SECONDS_COUNTDOWN, saved_state, msg)

    # ----------------------------------------
    # ui messages
    # ----------------------------------------
    def ad_ui_set_title(self, title=""):
        """

        :param title: 表示标题的内容
        :return:
        """
        msg = AtomAdSysctrl.mk_ad_set_title(title)
        return self.pub_state(WORLD_STATES.TITLE, title, msg)

    def ad_ui_set_logo(self, logo_url=""):
        """

        :param logo_url: 右下角的产品logo
        :return:
        """
        msg = AtomAdSysctrl.mk_ad_set_logo(logo_url)
        return self.pub_state(WORLD_STATES.LOGO, logo_url, msg)

    def ad_ui_set_round(self, round_number=""):
        """
        :param round_number: 表示当前轮的数字或字符
        """
        round_number = str(round_number)
        msg = AtomAdSysctrl.mk_ad_set_round(round_number)
        return self.pub_state(WORLD_STATES.ROUND, round_number, msg)

    def ad_ui_log_message(self, message_text, message_datetime=""):
        """

        :param message_text: 发送攻击记录的信息
        :param message_datetime: 可以带上时间，选填
        :return:
        """
        if not message_datetime:
            message_datetime = time.strftime('%Y-%m-%d %X', time.localtime())
        msg = AtomAdSysctrl.mk_ad_set_message(message_text, message_datetime)
        return self.pub_message(msg)

    def ad_ui_set_bottom(self, left_message, right_message=""):
        """

        :param left_message: 中下方的左边信息
        :param right_message: 中下方右边信息，选填
        :return:
        """
        msg = AtomAdSysctrl.mk_ad_set_ui_bottom(left_message, right_message)
        value = {"left": left_message, "right": right_message}
        return self.pub_state(WORLD_STATES.BOTTOM_TEXT, value, msg)
    
    def restore_countdown(self, saved_state):
        message = AtomAdSysctrl.mk_ad_sync_timing(saved_state['SECONDS'])
        self.pub_state(WORLD_STATES.TIME_SECONDS_COUNTDOWN, saved_state, message)