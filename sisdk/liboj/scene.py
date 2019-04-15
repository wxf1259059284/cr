#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-18 下午5:04
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : scene.py.py
# @Project : cpss

import sisdk.liboj.enums as oj_enums
import time
import logging
import threading
from .oj_behavior_pb2 import oj_task, oj_add_task_behavior
from sisdk.messages import wrap_message
from .atom_ojbehavior import AtomOjBehavior

try:#python2
    import Queue as queue
#建议按照python3的名字进行import

except ModuleNotFoundError:#python3
    import queue


class OjAction(object):
    def __init__(self, shipgroup_id, task_id_list, action=oj_enums.EnumOjActions.solve, member_seq=1,  # //队员id
                 result=False, score=0, is_first_blood=False):
        self.shipgroup_id = shipgroup_id
        self.task_id_list = task_id_list
        self.action = action
        self.member_seq = member_seq
        self.result = result
        self.score = score
        self.is_first_blood = is_first_blood

    def to_binary(self):
        if self.action == oj_enums.EnumOjActions.solve:
            msg = AtomOjBehavior.mk_oj_solv(shipgroup_id=self.shipgroup_id,
                                            task_id_list=self.task_id_list,
                                            member_seq=1,
                                            result=self.result,
                                            score=self.score,
                                            is_first_blood=self.is_first_blood)
        elif self.action == oj_enums.EnumOjActions.scan:
            msg = AtomOjBehavior.mk_oj_scan(shipgroup_id=self.shipgroup_id,
                                            task_id_list=self.task_id_list,
                                            member_seq=1)
        return msg

class OjShipgroup(object):
    def __init__(self, vis_obj, id, name, logo, members=2, priority=5):
        self.actions = queue.Queue()
        self.priority = priority  # 默认优先级别为5，更小将更先前，更大将更靠后
        self.life = 10  # 每个队伍的生命周期初始为30秒
        self.alive = False  # 从队列进入场景后alive设置为True
        self.vis_obj = vis_obj
        self.id = id
        self.name = name
        self.logo = logo
        self.members = members
        self.data_entities = {}
        self.data_flyout = {}
        self.max_shiplife = 30
        self.set_alive()
        # self.lock = threading.Lock()

    def to_proto(self):
        msg = AtomOjBehavior.mk_oj_shipgroup(self.id, self.name, self.members, self.logo, False)
        return msg

    def put_action(self, action):
        self.actions.put(action)
        if self.alive:
            if self.life < self.max_shiplife:
                self.life += 10  # 每有一个action出现，生命周期+10秒
                if self.life > self.max_shiplife:
                    self.life = self.max_shiplife

    def set_alive(self):
        self.alive = True
        msg_shipgroup = self.to_proto()
        msg_flyin = AtomOjBehavior.mk_oj_add_shipgroup(msg_shipgroup)
        self.vis_obj.pub_message(msg_flyin)
        logging.debug("Shipgroup %s flyin." % self.id)

        th_shipgroup = threading.Thread(name="OJ_Team_%s" % str(self.id), target=self.do_live)
        th_shipgroup.setDaemon(True)
        th_shipgroup.start()

    def do_live(self):
        while self.alive:
            try:
                # 如果队伍有动作没做完，这里处理一下
                if self.actions.qsize() > 0:
                    act = self.actions.get()
                    msg = act.to_binary()
                    self.vis_obj.pub_message(msg)
                    logging.debug("Getted action from shipgroup %s" % str(self.id))
            except Exception as e:
                logging.error("Error in ship.do_live:" + str(e))
            self.life -= 1
            #logging.debug("Shipgroup %s life -1 (%d/%d)" % (self.id, self.life, self.max_shiplife))
            if self.life < 1:
                self.alive = False
            time.sleep(1)
        msg_flyout = AtomOjBehavior.mk_oj_remove_shipgroup(self.id)
        # self.lock.acquire()
        self.vis_obj.pub_message(msg_flyout)
        # self.lock.release()
        logging.debug("Shipgroup %s flyout." % self.id)


class OjScene(object):
    def __init__(self, vis_obj):
        self.vis_obj = vis_obj
        self.tasks = []
        self.shipgroups = []    #TODO:shipgroup是否要分存活/未存活？未存活的要不要干掉，如何在队伍太多的时候控制一部分飞出去？

    def add_task(self, task_id, task_name,
                 task_type="",
                 score_init=0,
                 score_current=0,
                 solved_count=0,
                 ):
        task = {"task_id": str(task_id),
                "task_name": task_name,
                "task_type": task_type,
                "score_init": score_init,
                "score_current": score_current,
                "solved_count": solved_count}
        task_exists = False
        for t in self.tasks:
            if t["task_id"] == task_id:
                t.update(task)
                task_exists = True
        if not task_exists:
            self.tasks.append(task)

    def add_action(self, shipgroup_id, task_id, shipgroup_name="", shipgroup_logo="", shipgroup_members = -1,
                   priority = 5, action=oj_enums.EnumOjActions.solve, result=False, score=0, is_first_blood=False):
        shipgroup_exists = False
        for sg in self.shipgroups:
            if sg.id == shipgroup_id:
                if shipgroup_name: sg.name = shipgroup_name
                if shipgroup_logo: sg.logo = shipgroup_logo
                if shipgroup_members != -1: sg.members = shipgroup_members
                shipgroup_exists = True
        if not shipgroup_exists:
            sg = OjShipgroup(vis_obj=self.vis_obj,
                             id=shipgroup_id,
                             name=shipgroup_name,
                             logo=shipgroup_logo,
                             members=shipgroup_members,
                             priority=priority)
            self.shipgroups.append(sg)

        act = OjAction(shipgroup_id=shipgroup_id, task_id_list=[task_id], result=result, score=score,
                       action=action, is_first_blood=is_first_blood)
        for sg in self.shipgroups:
            if sg.id == shipgroup_id:
                sg.put_action(act)
                logging.debug("Putted action to shipgroup %s" % str(shipgroup_id))

    def to_binary(self):
        task_protos = []
        for t in self.tasks:
            t_proto = oj_task(**t)
            task_protos.append(t_proto)
        msg = oj_add_task_behavior(task=task_protos)
        return wrap_message(msg)
