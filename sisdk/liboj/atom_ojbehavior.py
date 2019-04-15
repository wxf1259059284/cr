#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午7:01
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_ojbehavior.py
# @Project : cpss

import sisdk.liboj.enums as oj_enum

from sisdk.liboj import oj_behavior_pb2
from sisdk.messages import wrap_message

class AtomOjBehavior(object):
    @staticmethod
    def mk_oj_scan(shipgroup_id, task_id_list, member_seq):
        msg = oj_behavior_pb2.oj_scan_behavior(src_obj_id=str(shipgroup_id),
                                               src_obj_child_id=str(member_seq),
                                               task_id=[str(id) for id in task_id_list])
        return wrap_message(msg)

    @staticmethod
    def mk_oj_solv(shipgroup_id, task_id_list, member_seq, result=False, score=0, is_first_blood=False):
        msg = oj_behavior_pb2.oj_solve_behavior(src_obj_id=str(shipgroup_id),
                                                task_id=[str(id) for id in task_id_list],
                                                src_obj_child_id=str(member_seq),
                                                result=result,
                                                score=score,
                                                is_first_blood=is_first_blood)
        return wrap_message(msg)


    @staticmethod
    def mk_oj_ai_scan():
        pass

    @staticmethod
    def mk_oj_task():
        pass

    @staticmethod
    def mk_oj_task_board():
        pass

    @staticmethod
    def mk_oj_team_board():
        pass

    @staticmethod
    def mk_oj_effects():
        pass

    @staticmethod
    def mk_oj_shipgroup(id, name, members=0, logo="", wrap=True):
        memb = []
        for i in range(1, members+1):
            msg_member = oj_behavior_pb2.oj_team_member(team_child_id=str(i), model=oj_enum.EnumVirtualModelType.vir_att_shipgroup)
            memb.append(msg_member)
        all_colors = [oj_enum.EnumOjColors.red,
                      oj_enum.EnumOjColors.yellow,
                      oj_enum.EnumOjColors.blue2,
                      oj_enum.EnumOjColors.orange,
                      oj_enum.EnumOjColors.purple,
                      oj_enum.EnumOjColors.green,
                      oj_enum.EnumOjColors.cyan,
                      oj_enum.EnumOjColors.magenta,
                      oj_enum.EnumOjColors.red2,
                      oj_enum.EnumOjColors.yellow2,
                      oj_enum.EnumOjColors.blue2,
                      oj_enum.EnumOjColors.orange2,
                      oj_enum.EnumOjColors.purple2,
                      oj_enum.EnumOjColors.green2]
        the_color = all_colors[int(id) % len(all_colors)]
        msg_shipgroup = oj_behavior_pb2.oj_team(team_id=str(id),
                                                team_name=name,
                                                color=the_color,
                                                team_members=memb,
                                                logo=logo,
                                                model=oj_enum.EnumVirtualModelType.vir_att_shipleader)
        if wrap:
            return wrap_message(msg_shipgroup)
        else:
            return msg_shipgroup

    @staticmethod
    def mk_oj_add_shipgroup(shipgroup_msg):
        msg = oj_behavior_pb2.oj_add_team_behavior(team=[shipgroup_msg])
        return wrap_message(msg)

    @staticmethod
    def mk_oj_remove_shipgroup(shipgroup_id):
        msg = oj_behavior_pb2.oj_remove_team_behavior(team_id=str(shipgroup_id))
        return wrap_message(msg)

    @staticmethod
    def mk_oj_add_task():
        pass