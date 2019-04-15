# -*- coding: utf-8 -*-
import sisdk.libmap.enums as Enums
from sisdk.libmap.atom_mapbehavior import AtomMapBehavior
from sisdk.messages import SequenceMessageMaker


class PackagedMessages(object):
    @staticmethod
    def map_attack(src_obj, dest_obj, attack_type, dest_type, attack_speed,  color, tail_width):

        msg_attack = AtomMapBehavior.mk_attack(src_obj, dest_obj, attack_type, dest_type, attack_speed, color, tail_width)

        return msg_attack

    @staticmethod
    def map_guideline(src_obj, dest_obj, dest_type, description='', color='#0099FF', duration=5):
        msg_guideline = AtomMapBehavior.mk_guideline(src_obj_id=src_obj, dest_obj_id=dest_obj,dest_type=dest_type,
                                                     description=description,
                                                     color=color, duration=duration)
        return msg_guideline

    @staticmethod
    def map_effect(src_obj, effect, duration, color1, color2, icon,  switch):
        msg_effect = AtomMapBehavior.mk_effect(src_obj_id=src_obj, effect=effect, duration=duration, color1=color1,
                                               color2=color2, icon=icon, switch=switch)

        return msg_effect

    @staticmethod
    def map_entity_panel():
        pass

    @staticmethod
    def map_move(src_obj, coordinates, move_speed, is_patrol):
        msg_move = AtomMapBehavior.mk_move(src_obj_id=src_obj, dest_coordinate=coordinates,
                                           move_speed=move_speed, is_patrol=is_patrol
                                           )
        return msg_move

    @staticmethod
    def map_set_entity_status(src_obj_id, color, switch):
        msg_status = AtomMapBehavior.mk_set_entity_status(
            src_obj_id=src_obj_id,
            color=color,
            switch=switch
        )
        return msg_status