#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午6:58
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_adsysctrl.py
# @Project : cpss

import time
import datetime
import sisdk.libad.enums as ad_enums

from sisdk.libad import ad_sysctrl_pb2
from sisdk.messages import wrap_message


class AtomAdSysctrl(object):
    @staticmethod
    def mk_ad_toggle_scene(scenario_type=ad_enums.EnumScenarioType.virtual_starwar, play_movie=True):
        msg = ad_sysctrl_pb2.ad_sysctrl_toggle_scene(scenario_type=scenario_type, play_movie=play_movie)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_toggle_camera(camera_type=ad_enums.EnumCameraType.normal):
        msg = ad_sysctrl_pb2.ad_sysctrl_toggle_camera(camera_type=camera_type)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_toggle_panel(panel_type=ad_enums.EnumPanelType.all_panels, action=ad_enums.EnumShowHide.show):
        msg = ad_sysctrl_pb2.ad_sysctrl_toggle_panel(panel_type=panel_type, action=action)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_sync_timing(countdown_time=0):
        # TODO:在回放时，应当关闭自动倒数
        d = datetime.datetime.now()
        weekday = d.weekday()
        the_week = u'星期' + [u'一', u'二', u'三', u'四', u'五', u'六', u'日'][weekday]
        the_date = d.strftime('%Y-%m-%d')
        server_time = int(time.time() * 1000)
        msg = ad_sysctrl_pb2.ad_sysctrl_sync_timing(the_week=the_week,
                                  the_date=the_date,
                                  countdown_time=countdown_time,
                                  server_time=server_time,
                                  display_countdown=True)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_set_title(title_text="untitled"):
        msg = ad_sysctrl_pb2.ad_sysctrl_set_title(title_text=title_text)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_set_logo(logo_url=""):
        msg = ad_sysctrl_pb2.ad_sysctrl_set_logo(logo_url=logo_url)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_set_round(round_text="N"):
        msg = ad_sysctrl_pb2.ad_sysctrl_set_round(round_text=round_text)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_set_ui_bottom(left_message, right_message=""):
        if right_message:
            str_message = left_message + '|' + right_message
        else:
            str_message = left_message
        msg = ad_sysctrl_pb2.ad_sysctrl_set_ui_bottom(bottom_text=str_message)
        return wrap_message(msg)

    @staticmethod
    def mk_ad_set_message(message="", datetime=""):
        msg = ad_sysctrl_pb2.ad_sysctrl_set_message(message_text=message, datetime=datetime)
        return wrap_message(msg)