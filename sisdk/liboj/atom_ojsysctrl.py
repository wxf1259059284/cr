#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-4 下午7:01
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_ojsysctrl.py
# @Project : cpss
from sisdk.liboj import oj_sysctrl_pb2
from sisdk.messages import wrap_message


class AtomOjSysctrl(object):
    @staticmethod
    def mk_oj_toggle_camera():
        pass

    @staticmethod
    def mk_oj_toggle_panel():
        pass

    @staticmethod
    def mk_oj_sync_timing():
        pass

    @staticmethod
    def mk_oj_set_title(title_text="untitled"):
        msg = oj_sysctrl_pb2.oj_sysctrl_set_title(title_text=title_text)
        return wrap_message(msg)

    @staticmethod
    def mk_oj_set_logo(logo_url=""):
        msg = oj_sysctrl_pb2.oj_sysctrl_set_logo(logo_url=logo_url)
        return wrap_message(msg)

    @staticmethod
    def mk_oj_set_round(round_text="N"):
        msg = oj_sysctrl_pb2.oj_sysctrl_set_round(round_text=round_text)
        return wrap_message(msg)

    @staticmethod
    def mk_oj_set_ui_bottom(left_message, right_message=""):
        if right_message:
            str_message = left_message + '|' + right_message
        else:
            str_message = left_message
        msg = oj_sysctrl_pb2.oj_sysctrl_set_ui_bottom(bottom_text=str_message)
        return wrap_message(msg)

    @staticmethod
    def mk_oj_sync_timing(countdown_time=0):
        msg = oj_sysctrl_pb2.oj_sysctrl_set_timer(countdown_time=countdown_time)
        return wrap_message(msg)

    @staticmethod
    def mk_oj_set_message(message="", datetime=""):
        msg = oj_sysctrl_pb2.oj_sysctrl_set_message(message_text=message, datetime=datetime)
        return wrap_message(msg)
