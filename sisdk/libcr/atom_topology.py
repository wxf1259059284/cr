#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-22 下午7:47
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_topology.py.py
# @Project : cpss


import random
from .enums import EnumAttackIntensity, EnumSandtableEffect, EnumOnoff, EnumTopologyEffect
from .cr_topology_pb2 import (topology_attack, topology_effect, topology_guide_line, topology_entity_panel) #, topology_game_settings)
from sisdk.messages import wrap_message

topology_init_data = [{"obj_id":"unit1", "obj_name":u"红方"},
                       {"obj_id":"unit2", "obj_name":u"红方"}]


class AtomTopology(object):
    @staticmethod
    def mk_topology_setting():
        # setting = topology_camera_settings(normalY=18,
        #                                    roamingFootY=19,
        #                                    roamingPeakY=20)
        # return wrap_message(setting)
        pass

    @staticmethod
    def mk_topology_init(topo_id=1):
        if topo_id == 1:
            msg = topo1.to_protobuf()
        else:
            #TODO:其它种类的拓扑
            msg = topo2.to_protobuf()
        return wrap_message(msg)

    @staticmethod
    def mk_topology_attack(switch=EnumOnoff.on,
                            intensity=EnumAttackIntensity.attack_moderate,
                            src_obj_id="",
                            dest_obj_id="",
                            color="#FFFFFF",
                            duration=4,
                            wrap=True):
        msg = topology_attack(switch=switch,
                              intensity=intensity,
                              src_obj_id=src_obj_id,
                              dest_obj_id=dest_obj_id,
                              color="#" + color,
                              duration=duration)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_topology_effect(switch=EnumOnoff.on,
                            effect = EnumTopologyEffect.blink,
                            src_obj_id="",
                            icon="",
                            color1="NOT_SET",
                            color2="NOT_SET",
                            duration=4,
                            wrap=True):

        if src_obj_id == "":
            src_obj_id = random.choice(topology_init_data)["obj_id"]
        msg = topology_effect(switch = switch,
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
    def mk_topology_guideline(switch=EnumOnoff.on,
                               src_obj_id="NOT_SET",
                               dest_obj_id="NOT_SET",
                               duration=5,
                               color="FFFFFF",
                               wrap=True):
        msg = topology_guide_line(switch=switch,
                                   src_obj_id=src_obj_id,
                                   dest_obj_id=dest_obj_id,
                                   duration=duration,
                                  color="#" + color)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_topology_entity_panel(src_obj_id="", switch=EnumOnoff.on, ip_address="", os_name="", status="", duration=0,wrap=True):
        msg = topology_entity_panel(src_obj_id=src_obj_id,
                                    switch=switch,
                                    ip_address=ip_address,
                                    os_name=os_name,
                                    status=status,
                                    duration=duration)
        if wrap:
            return wrap_message(msg)
        else:
            return msg