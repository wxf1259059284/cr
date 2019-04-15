#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-22 下午7:49
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : packaged_messages.py
# @Project : cpss

import random
import sisdk.libcr.enums as Enums
from sisdk.messages import SequenceMessageMaker
from sisdk.libcr.atom_topology import AtomTopology
from sisdk.libcr.atom_sandtable import AtomSandTable

class PackagedMessages(object):

    @staticmethod
    def topo_attack(src_obj, dest_obj, success=True, show_guildline=True,
                    show_panel=False, panel_text="", panel_os="",
                    change_color=False, show_top_icon=False):
        if success:
            color = "FF3300"
            icon = Enums.EnumEffectIcon.exclamation
            effect = Enums.EnumTopologyEffect.bubble
        else:
            color = "00CCFF"
            icon = Enums.EnumEffectIcon.information
            effect = Enums.EnumTopologyEffect.defence
        msg_attack = AtomTopology.mk_topology_attack(src_obj_id=src_obj, dest_obj_id=dest_obj, duration=5, color=color, wrap=False)
        msg_guideline = AtomTopology.mk_topology_guideline(src_obj_id=src_obj, dest_obj_id=dest_obj, duration=8,
                                              color=color, wrap=False)
        msg_attacked_effect = AtomTopology.mk_topology_effect(switch=Enums.EnumOnoff.on, icon=icon, src_obj_id=dest_obj, effect=effect,
                                                 color1=color, duration=2, wrap=False)
        msg_panel = AtomTopology.mk_topology_entity_panel(switch=Enums.EnumOnoff.on, src_obj_id=dest_obj, ip_address=dest_obj,
                                             status=panel_text, duration=2, wrap=False,
                                             os_name=panel_os)
        msg_change_color = AtomTopology.mk_topology_effect(switch=Enums.EnumOnoff.on, icon=icon, src_obj_id=dest_obj,
                                              effect=Enums.EnumTopologyEffect.change_color,
                                              color1=color, duration=0, wrap=False)
        msg_topicon = AtomTopology.mk_topology_effect(switch=Enums.EnumOnoff.on, effect=Enums.EnumTopologyEffect.icon_indicator, icon=icon,
                                         color1=color, wrap=False, src_obj_id=dest_obj, duration=0)
        smq = SequenceMessageMaker(Enums.EnumMessageType.behavior, Enums.EnumScenarioType.topology)
        if show_guildline:
            smq.add_fragment(msg_guideline)
        smq.add_fragment(msg_attack)
        smq.add_fragment(msg_attacked_effect, 1)
        if change_color:
            smq.add_fragment(msg_change_color)
        if show_panel:
            smq.add_fragment(msg_panel, 1)
        if show_top_icon:
            smq.add_fragment(msg_topicon)

        msg = smq.serialized()
        return msg

    @staticmethod
    def topo_guideline(src_obj, dest_obj, color, duration):
        msg_guideline = AtomTopology.mk_topology_guideline(src_obj_id=src_obj, dest_obj_id=dest_obj, color=color, duration=duration)
        return msg_guideline

    @staticmethod
    def topo_effect(obj, effect, color1, color2):
        msg_effect = AtomTopology.mk_topology_effect(src_obj_id=obj, icon=Enums.EnumEffectIcon.information,
                                                     effect=effect, color1=color1, color2=color2)
        return msg_effect

    @staticmethod
    def topo_show_entity_panel(obj, os_name,  panel_text):
        msg_panel = AtomTopology.mk_topology_entity_panel(src_obj_id=obj, ip_address=obj, status=panel_text,
                                                          os_name=os_name)
        return msg_panel

    @staticmethod
    def topo_show_entity_icon(obj, icon, color):
        msg_topicon = AtomTopology.mk_topology_effect(effect=Enums.EnumTopologyEffect.icon_indicator,
                                                      icon=icon,  color1=color, src_obj_id=obj, duration=0)
        return msg_topicon


    @staticmethod
    def sandtable_attack(src_obj, dest_obj, success=True, show_guildline=True, icon=Enums.EnumEffectIcon.information,
                         change_indicators=False, percentage_inner=0,percentage_outer=0, top_text=""):
        if success:
            effect = Enums.EnumSandtableEffect.charge
            icon = Enums.EnumEffectIcon.exclamation
            color = "FF3300"
        else:
            effect = Enums.EnumSandtableEffect.defence
            icon = Enums.EnumEffectIcon.information
            color = "00CCFF"

        m_guildline = AtomSandTable.mk_sandtable_guideline(switch=Enums.EnumOnoff.on,
                                             src_obj_id=src_obj,
                                             dest_obj_id=dest_obj,
                                             duration=5,
                                             color=color,
                                             wrap=False)
        m_attack = AtomSandTable.mk_sandtable_attack(attack_speed=10,
                                                     src_obj_id=src_obj,
                                                     dest_obj_id=dest_obj,
                                                     color=color,
                                                     size=15,
                                                     tail_duration=10,
                                                     wrap=False)
        m_effect = AtomSandTable.mk_sandtable_effect(switch=Enums.EnumOnoff.on,
                                       effect=effect,
                                       src_obj_id=dest_obj,
                                       icon=icon,
                                       duration=10,
                                       wrap=False)
        m_panel = AtomSandTable.mk_sandtable_panel(src_obj_id=dest_obj, icon=icon,
                                     top_text=top_text,
                                     per1=percentage_inner,
                                     per2=percentage_outer,
                                     wrap=False)
        smq = SequenceMessageMaker(Enums.EnumMessageType.behavior, Enums.EnumScenarioType.sandtable)
        if show_guildline:
            smq.add_fragment(m_guildline)
        smq.add_fragment(m_attack)
        smq.add_fragment(m_effect, 1)
        if change_indicators:
            smq.add_fragment(m_panel)
        msg = smq.serialized()
        return msg

    @staticmethod
    def sandtable_guideline(src_obj, dest_obj, color, duration):
        m_guildline = AtomSandTable.mk_sandtable_guideline(src_obj_id=src_obj, dest_obj_id=dest_obj,
                                                           duration=duration, color=color)
        return m_guildline

    @staticmethod
    def sandtable_effect(src_obj, effect, duration, color1, color2):
        m_effect = AtomSandTable.mk_sandtable_effect(effect=effect, src_obj_id=src_obj,
                                                     icon=Enums.EnumEffectIcon.exclamation, duration=duration,
                                                     color1=color1, color2=color2)
        return m_effect

    @staticmethod
    def sandtable_updta_top_icon(src_obj, icon, top_text, percentage_inner, percentage_outer):
        m_panel = AtomSandTable.mk_sandtable_panel(src_obj_id=src_obj, icon=icon, top_text=top_text,
                                                   per1=percentage_inner,
                                                   per2=percentage_outer)
        return m_panel



