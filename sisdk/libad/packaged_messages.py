#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-16 下午12:03
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : packaged_messages.py.py
# @Project : cpss


import sisdk.libad.enums as ad_enums
from .atom_adbehavior import AtomAdBehavior

class PackagedMessages(object):
    @staticmethod
    def attack(src_team_id, dest_team_id, dest_unit_id,
               intensity=ad_enums.EnumAttackIntensity.attack_moderate,
               success=False, firstblood=False, src_score=0, dest_score=0, color="red"):
        src_unit_id = "dummy-%s" % str(src_team_id)
        dest_unit_id = "unit-%s-%s" % (str(dest_team_id), str(dest_unit_id))

        if firstblood:
            intensity = ad_enums.EnumAttackIntensity.attack_charge   #应是charge

        msg_attack = AtomAdBehavior.mk_ad_attack(src_team_id=src_team_id,
                                                 src_unit_id=src_unit_id,
                                                 dest_team_id=dest_team_id,
                                                 dest_unit_id=dest_unit_id,
                                                 intensity=intensity,
                                                 is_firstblood=firstblood,
                                                 is_defensed = (not success),
                                                 src_score=src_score,
                                                 dest_score=dest_score,
                                                 color=color,
                                                 wrap=True)

        return msg_attack

    @staticmethod
    def arbiter_attack(dest_team_id, dest_unit_id,
                       attack_intensity=ad_enums.EnumAttackIntensity.attack_moderate,
                       dest_score=0):
        dest_unit_id = "unit-%s-%s" % (str(dest_team_id), str(dest_unit_id))
        msg_attack = AtomAdBehavior.mk_ad_attack(src_team_id="NPC.arbiter",
                                                 src_unit_id="",
                                                 dest_team_id=dest_team_id,
                                                 dest_unit_id=dest_unit_id,
                                                 intensity=attack_intensity,
                                                 dest_score=dest_score,
                                                 wrap=True)
        return msg_attack

    @staticmethod
    def puzzle_attack(src_team_id, dest_puzzle_id, success=False, firstblood=False,
                      src_score=0):
        if success:
            color = "green"
        else:
            color = "red"
        src_unit_id = "dummy-%s" % str(src_team_id)
        msg_attack = AtomAdBehavior.mk_ad_attack(src_team_id=src_team_id,
                                                 src_unit_id=src_unit_id,
                                                 dest_team_id="NPC.puzzle",
                                                 dest_unit_id=dest_puzzle_id,
                                                 color=color,
                                                 intensity=ad_enums.EnumAttackIntensity.attack_gather,
                                                 is_defensed=(not success),
                                                 is_firstblood=firstblood,
                                                 src_score=src_score,
                                                 dest_score=0,
                                                 wrap=True)
        return msg_attack
