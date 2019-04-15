#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-15 上午11:19
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_mapsysctrl.py
# @Project : cpss
import datetime
import time
from map_sysctrl_pb2 import sysctrl_sync_timing, sysctrl_set_message
from enums import EnumOnoff, EnumPosition, EnumToastIcon, EnumMapMark
from sisdk.libmap import map_sysctrl_pb2
from sisdk.messages import wrap_message


class MapSysctrl(object):
    @staticmethod
    def mk_toggle_camera(camera_type=0):
        pass

    @staticmethod
    def mk_focus(obj_id, obj_id2="", obj_id3="", duration=1000, switch=EnumOnoff.on):
        msg = map_sysctrl_pb2.sysctrl_focus(
            obj_id1=obj_id,
            duration=duration,
            switch=switch
        )
        return wrap_message(msg)

    @staticmethod
    def mk_set_message_extend(message="", src_team="", src_ip="", dest_team="", dest_ip=""):
        msg = sysctrl_set_message(src_team=src_team, src_ip=src_ip, dest_team=dest_team, dest_ip=dest_ip,
                                  message_text=message,
                                  datetime=time.strftime('%Y-%m-%d %X', time.localtime()))
        return wrap_message(msg)

    @staticmethod
    def mk_sync_timing(display_countdown=True, astro_time='', countdown_time=0):
        d = datetime.datetime.now()
        weekday = d.weekday()
        the_week = u'星期' + [u'一', u'二', u'三', u'四', u'五', u'六', u'日'][weekday]
        the_date = d.strftime('%Y-%m-%d')
        server_time = int(time.time())
        msg = sysctrl_sync_timing(the_week=the_week,
                                  the_date=the_date,
                                  countdown_time=countdown_time,
                                  server_time=server_time,
                                  display_countdown=display_countdown,
                                  astro_time=astro_time)
        return wrap_message(msg)

    @staticmethod
    def mk_set_timing_labels(left_timing_label, right_timing_label):
        msg = map_sysctrl_pb2.sysctrl_timing_labels(left_timing_label=left_timing_label,
                                                    right_timing_label=right_timing_label)
        return wrap_message(msg)

    @staticmethod
    def mk_set_title(title_text="untitled"):
        msg = map_sysctrl_pb2.sysctrl_set_title(title_text=title_text)
        return wrap_message(msg)

    @staticmethod
    def mk_set_logo(logo_url=""):
        msg = map_sysctrl_pb2.sysctrl_set_logo(logo_url=logo_url)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_toast(position=EnumPosition.left, icon=EnumToastIcon.information, text_title="untitled",
                    text_content="sample content", switch=EnumOnoff.on, duration=5, color=""):
        if position == EnumPosition.top:
            alpha = 1.0
        else:
            alpha = 0.8
        if not color:
            color = color
        msg = map_sysctrl_pb2.sysctrl_toast(positon=position,
                                            icon=icon,
                                            text_title=text_title,
                                            text_content=text_content,
                                            switch=switch,
                                            duration=duration,
                                            message_id=str(time.time()),
                                            color=color,
                                            alpha=alpha)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_set_message(message="", datetime=""):
        msg = map_sysctrl_pb2.sysctrl_set_message(message_text=message, datetime=datetime)
        return wrap_message(msg)

    @staticmethod
    def mk_map_mark(name, longitude, latitude, mark_type=EnumMapMark.country):
        msg = map_sysctrl_pb2.map_mark(
            mark_type=mark_type,
            longitude=longitude,
            latitude=latitude,
            name=name
        )
        return wrap_message(msg)

    @staticmethod
    def mk_map_settings(map_type, color):
        msg = map_sysctrl_pb2.map_settings(
            type=map_type,
            color=color,
        )
        return wrap_message(msg)