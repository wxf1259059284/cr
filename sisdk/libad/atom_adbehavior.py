#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午6:58
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_adbehavior.py
# @Project : cpss

import sisdk.libad.enums as ad_enums
from sisdk.libad import ad_behavior_pb2
from sisdk.messages import wrap_message

class AtomAdBehavior(object):
    @staticmethod
    def mk_ad_damages(team_id, unit_id, occupied=False, pwn=False, down=False, wrap=True):
        msg = ad_behavior_pb2.ad_damages(team_id=team_id, unit_id=unit_id,
                                         occupied=occupied, pwn=pwn, down=down)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_ad_attack(src_team_id, src_unit_id, dest_team_id, dest_unit_id,
                     intensity=ad_enums.EnumAttackIntensity.attack_moderate,
                     color=ad_enums.EnumColor.blue,
                     gather_action=False, is_defensed=False,
                     is_firstblood=False, src_score = 0, dest_score=0,
                     wrap=True):
        msg = ad_behavior_pb2.ad_attack(src_team_id=str(src_team_id),
                                        src_unit_id=str(src_unit_id),
                                        dest_team_id=str(dest_team_id),
                                        dest_unit_id=str(dest_unit_id),
                                        intensity=intensity,
                                        color=color,
                                        is_puzzle=gather_action,
                                        is_defensed=is_defensed,
                                        is_firstblood=is_firstblood,
                                        src_score=src_score,
                                        dest_score=dest_score)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_ad_effect(team_id, team_child_id,
                     switch=ad_enums.EnumOnoff.on,
                     effect=ad_enums.EnumAdEffect.defence,
                     color=ad_enums.EnumColor.blue,
                     duration=5, wrap=True):
        msg = ad_behavior_pb2.ad_effect(team_id=str(team_id),
                                        team_child_id=str(team_child_id),
                                        effect=effect,
                                        switch=switch,
                                        color=color,
                                        duration=duration)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_ad_team_score_action(team_id, unit_id, score, wrap=True):
        msg = ad_behavior_pb2.ad_team_score_aciton(team_id=team_id,
                                                   team_child_id=unit_id,
                                                   score=score)
        if wrap:
            return wrap_message(msg)
        else:
            return msg
