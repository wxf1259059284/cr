#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @date: 2018/6/10 09:30
# @author：Ivan Wang

import random
from sisdk.libcr.enums import (EnumEffectIcon,
                               EnumAttackIntensity, EnumOnoff, EnumSandtableEffect, EnumShowHide)
from .cr_sandtable_pb2 import (sandtable_attack, sandtable_settings, sandtable_entity,
        sandtable_effects, sandtable_panel, sandtable_arbiter_show_hide, sandtable_guide_line)
from .base_pb2 import camera_settings
from sisdk.messages import wrap_message

sandtable_init_data = [{"preset_point":"point_1", "obj_id":"t-1", "obj_name":u"红方"},
                       {"preset_point":"point_2", "obj_id":"t-2", "obj_name":u"蓝方"}]

class AtomSandTable(object):
    @staticmethod
    def mk_sandtable_setting():
        setting = sandtable_settings()
        return wrap_message(setting)

    @staticmethod
    def mk_sandtable_init():
        msg_camera_settings = camera_settings(normalY=150.0,  # normal 镜头轨道的Y坐标
                                              roamingFootY=50.0,  # Roaming 镜头轨道低Y坐标
                                              roamingPeakY=50.0,  # Roaming 镜头轨道高Y坐标
                                              trackScale=4.0)  # Track Scale
        msg_init = sandtable_settings(camera_settings=msg_camera_settings)
        entities = []
        for d in sandtable_init_data:
            entity = sandtable_entity(preset_point_id=d["preset_point"],
                                      set_obj_id=d["obj_id"],
                                      set_obj_name=d["obj_name"])
            entities.append(entity)
        msg_init.legend = "Red Vs. Blue"
        msg_init.entities.extend(entities)
        return wrap_message(msg_init)

    @staticmethod
    def mk_sandtable_attack(intensity=EnumAttackIntensity.attack_moderate,
                            attack_speed=0,
                            src_obj_id="",
                            dest_obj_id="",
                            color="",
                            size=2,
                            tail_duration=2,
                            wrap=True):
        msg = sandtable_attack(intensity=intensity,
                               attack_speed=attack_speed,
                               src_obj_id=src_obj_id,
                               dest_obj_id=dest_obj_id,
                               color="#" + color,
                               size=size,
                               tail_duration=tail_duration)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_sandtable_effect(switch=EnumOnoff.on,
                            effect=EnumSandtableEffect.blink,
                            src_obj_id="",
                            icon="",
                            color1="NOT_SET",
                            color2="NOT_SET",
                            duration=4,
                            wrap=True):

        if src_obj_id == "":
            src_obj_id = random.choice(sandtable_init_data)["obj_id"]
        msg = sandtable_effects(switch = switch,
                                effect = effect,
                                src_obj_id = src_obj_id,
                                icon=icon,
                                color1 = "#" + color1,
                                color2 = "#" + color2,
                                duration = duration)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_sandtable_guideline(switch=EnumOnoff.on,
                               src_obj_id="NOT_SET",
                               dest_obj_id="NOT_SET",
                               duration=5,
                               color="666666",
                               wrap=True):
        msg = sandtable_guide_line(switch=switch,
                                   src_obj_id=src_obj_id,
                                   dest_obj_id=dest_obj_id,
                                   duration=duration,
                                   color="#" + color)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_sandtable_arbiter_showhide(act=EnumShowHide.show):
        msg = sandtable_arbiter_show_hide(action=act)
        return wrap_message(msg)

    @staticmethod
    def mk_sandtable_panel(src_obj_id="",
                           icon=EnumEffectIcon.information,
                           top_text="N/A",
                           per1=0.2,
                           per2=0.3,
                           wrap=True):
        msg = sandtable_panel(src_obj_id=src_obj_id, icon=icon, top_text=top_text, percentage1=per1, percentage2=per2)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

if __name__ == "__main__":
    msg1 = sandtable_attack(src_obj_id="unit1", dest_obj_id="unit2")
    st = msg1.SerializeToString()
    msg2 = sandtable_attack()
    msg2.ParseFromString(st)
    msg2