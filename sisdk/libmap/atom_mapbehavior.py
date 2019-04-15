#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-15 上午11:18
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_mapbehavior.py
# @Project : cpss
import enums as map_enums
from sisdk.libmap import map_behavior_pb2
from sisdk.libmap.mapscene import ModelPos, ModelDestObject
from sisdk.messages import wrap_message


class AtomMapBehavior(object):
    @staticmethod
    def mk_attack(src_obj, dest_obj, attack_type, dest_type, attack_speed, color, tail_width, switch=map_enums.EnumOnoff.on,
                  wrap=True):
        msg = map_behavior_pb2.attack(switch=switch,
                                      type=attack_type,
                                      speed=attack_speed,
                                      src_id=str(src_obj),
                                      dest=ModelDestObject(dest_type, dest_obj).to_protobuf(),
                                      color=color,
                                      tail_len=1.2,
                                      tail_width=tail_width)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_guideline(src_obj_id, dest_obj_id, dest_type=map_enums.EnumDestType.entity, description='',
                     switch=map_enums.EnumOnoff.on, duration=5, color='#0099FF', wrap=True):
        msg = map_behavior_pb2.guide_line(src_id=str(src_obj_id),
                                          dest=ModelDestObject(dest_type=dest_type,
                                                               dest_id=dest_obj_id).to_protobuf(),
                                          switch=switch,
                                          duration=duration,
                                          color=color,
                                          description=description,
                                          )
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_move(src_obj_id, dest_coordinate, sleep_time=10, isOrbitMove=False, start_coordinate=None,
                end_coordinate=None, move_speed=4,
                switch=map_enums.EnumOnoff.on, is_patrol=True, wrap=True):
        dest_points = []
        for dest_point in dest_coordinate:
            a, b, c = dest_point
            dest_point = ModelPos(a, b, c).to_protobuf()
            if isOrbitMove:
                start_a, start_b, start_c = start_coordinate
                start_coordinate = ModelPos(start_a, start_b, start_c).to_protobuf()
                end_a, end_b, end_c = end_coordinate
                end_coordinate = ModelPos(end_a, end_b, end_c).to_protobuf()
            move_way = map_behavior_pb2.move.move_way(pos=dest_point,
                                                      sleep_time=sleep_time,
                                                      isOrbitMove=isOrbitMove,
                                                      orbit_start_pos=start_coordinate,
                                                      orbit_end_pos=end_coordinate
                                                      )
            dest_points.append(move_way)
        move_message = map_behavior_pb2.move(
            switch=switch,
            obj_id=src_obj_id,
            move_waypoint=dest_points,
            move_speed=move_speed,
            is_patrol=is_patrol,
        )
        if wrap:
            return wrap_message(move_message)
        else:
            return move_message

    @staticmethod
    def mk_effect(src_obj_id, color1="", color2="", switch=map_enums.EnumOnoff.on,
                  effect=map_enums.EnumSandtableEffect.enhance, icon=map_enums.EnumEffectIcon.information,
                  duration=5, wrap=True):
        msg = map_behavior_pb2.behavior_effect(src_obj_id=str(src_obj_id),
                                               color1=color1,
                                               color2=color2,
                                               switch=switch,
                                               effect=effect,
                                               icon=icon,
                                               duration=duration)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_entity_panel(src_obj_id, text, duration, switch=map_enums.EnumOnoff.on, wrap=True):
        msg = map_behavior_pb2.entity_panel(
            src_obj_id=src_obj_id,
            describe=text,
            duration=duration,
            switch=switch,
        )
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_set_entity_status(src_obj_id, color, switch, wrap=True):
        msg = map_behavior_pb2.set_entity_status(
            id=src_obj_id,
            show_flag=switch,
            color=color
        )
        if wrap:
            return wrap_message(msg)
        else:
            return msg