#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @date: 2018/5/30 15:32
# @name: atom_sysctrl.py
# @author：Ivan Wang

import time
import datetime
from .enums import EnumOnoff
from .base_pb2 import camera_settings
from .cr_sysctrl_pb2 import (sysctrl_toggle_scene, sysctrl_toggle_camera, sysctrl_sync_timing, sysctrl_focus,
                   sysctrl_set_message,  sysctrl_focus_subnet)
from sisdk.messages import wrap_message

class AtomSysctrl(object):
    @staticmethod
    def mk_toggle_scene(scenario_type=1, play_movie=True):
        msg = sysctrl_toggle_scene(scenario_type=scenario_type, play_movie=play_movie)
        return wrap_message(msg)

    @staticmethod
    def mk_toggle_camera(camera_type=0):
        msg = sysctrl_toggle_camera(camera_type=camera_type)
        return wrap_message(msg)

    @staticmethod
    def mk_focus(obj_id1, obj_id2="", obj_id3="", duration=10, switch=EnumOnoff.on):
        msg = sysctrl_focus(obj_id1=obj_id1,
                            obj_id2=obj_id2,
                            obj_id3=obj_id3,
                            duration=duration,
                            switch=switch)
        return wrap_message(msg)

    @staticmethod
    def mk_focus_subnet(subnet_id, duration, switch=EnumOnoff.on, wrap=True):
        msg_camera_settings = camera_settings(normalY = 150.0,				# normal 镜头轨道的Y坐标
                                              roamingFootY = 50.0,			# Roaming 镜头轨道低Y坐标
                                              roamingPeakY = 50.0,			# Roaming 镜头轨道高Y坐标
                                              trackScale= 4.0)               # Track Scale
        msg = sysctrl_focus_subnet(subnet_id=subnet_id, duration=duration, switch=switch, camera_settings=msg_camera_settings)
        if wrap:
            return wrap_message(msg)
        else:
            return msg

    @staticmethod
    def mk_set_message_extend(message="", src_team="", src_ip="", dest_team="", dest_ip=""):
        msg = sysctrl_set_message(src_team=src_team, src_ip=src_ip, dest_team=dest_team, dest_ip=dest_ip,
                                  message_text=message,
                                  datetime=time.strftime('%Y-%m-%d %X', time.localtime()))
        return wrap_message(msg)

    @staticmethod
    def mk_sync_timing(display_countdown=True, countdown_time=0):
        # TODO:如果到0点以后，这个信息要更新到第二天
        # TODO:在回放时，应当关闭自动倒数
        d = datetime.datetime.now()
        weekday = d.weekday()
        the_week = u'星期' + [u'一', u'二', u'三', u'四', u'五', u'六', u'日'][weekday]
        the_date = d.strftime('%Y-%m-%d')
        server_time = int(time.time())
        msg = sysctrl_sync_timing(the_week=the_week,
                                  the_date=the_date,
                                  countdown_time=countdown_time,
                                  server_time=server_time,
                                  display_countdown=display_countdown)
        return wrap_message(msg)