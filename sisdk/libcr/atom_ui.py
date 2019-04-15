#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @date: 2018/5/30 15:32
# @name: atom_sysctrl.py
# @author：Ivan Wang

import datetime
import time
import sisdk.libcr.enums as Enums
from .base_pb2 import playback_events, playback_progress
from .cr_ui_pb2 import ui_html_panel, ui_chart_init, ui_chart_update
from .cr_sysctrl_pb2 import (sysctrl_toggle_panel, sysctrl_set_title, sysctrl_set_logo, sysctrl_sync_timing,
                            sysctrl_toast, sysctrl_set_message, sysctrl_scoreboard)
from sisdk.messages import wrap_message

legends = [('red','红方'), ('blue','蓝方'), ('white','白方')]


class AtomUi(object):
    @staticmethod
    def mk_ui_html_panel_show(id, url, title="", width=640, height=480, closable=False, posX=400, posY=300):
        msg = ui_html_panel(action=Enums.EnumHtmlPanelAction.show, id=id, url=url, title=title,
                            posX=posX, posY=posY, width=width, height=height, closable=closable)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_html_panel_hide(id):
        msg = ui_html_panel(action=Enums.EnumHtmlPanelAction.hide, id=id)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_html_panel_close(id):
        msg = ui_html_panel(action=Enums.EnumHtmlPanelAction.close, id=id)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_html_panel_reload(id):
        msg = ui_html_panel(action=Enums.EnumHtmlPanelAction.reload, id=id)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_toggle_panel(panel_type=0, action=1):     # 定义在了sysctrl里，实际上是UI相关，先在包装层放在ui里。
        msg = sysctrl_toggle_panel(panel_type=panel_type, action=action)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_sync_timing(display_countdown=True):
        d = datetime.datetime.now()
        weekday = d.weekday()
        the_week = u'星期' + [u'一', u'二', u'三', u'四', u'五', u'六', u'日'][weekday]
        the_date = d.strftime('%Y-%m-%d')
        countdown_time = 4600000
        server_time = int(time.time() * 1000)
        msg = sysctrl_sync_timing(the_week=the_week,
                                  the_date=the_date,
                                  countdown_time=countdown_time,
                                  server_time=server_time,
                                  display_countdown=display_countdown)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_toast(position=Enums.EnumPosition.left, icon=Enums.EnumToastIcon.information, text_title="untitled",
                 text_content="sample content", switch=Enums.EnumOnoff.on, duration=5, color=""):
        if position == Enums.EnumPosition.top:
            alpha = 1.0
        else:
            alpha = 0.8
        if not color:
            color = color
        msg = sysctrl_toast(positon=position,
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
    def mk_ui_set_title(title_text="untitled"):
        msg = sysctrl_set_title(title_text=title_text)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_set_logo(logo_url=""):
        msg = sysctrl_set_logo(logo_url=logo_url)
        return wrap_message(msg)

    @staticmethod
    def mk_playback_events(eventlist=[]):
        """
        :param eventlist: [{"position":0.23, "event_title":"", "event_description":"hh", "knob_color":"white"}]
        """
        msg_events = []
        for event in eventlist:
            msg_event = playback_events.event_info(position=event['position'],
                                                           event_title=event['event_title'],
                                                           event_description=event['event_description'],
                                                           knob_color=event['knob_color'])
            msg_events.append(msg_event)
        msg_pb_events = playback_events(events=msg_events)
        return wrap_message(msg_pb_events)

    @staticmethod
    def mk_playback_progress(progress_action=Enums.EnumProgressAction.play, progress_value=0, speed_value=0):
        msg = playback_progress(action=progress_action,
                                progress_value=progress_value,
                                speed_value=speed_value)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_set_message(message="", datetime=""):
        msg = sysctrl_set_message(message_text=message,
                                  datetime=datetime)
        return wrap_message(msg)

    @staticmethod
    def mk_ui_scoreboard(objects=[], title="The Scoreboard"):
        """
        :param objects: [{"id": "xx", "name":"xx", "score":100, "mvp": "xx", "trend": enum_trend, "country_flag": "", "rank": 1, "fbc": 2, "logo":"http://xx"]}
        """
        score_infos = []
        for obj in objects:
            scoreboard_info = sysctrl_scoreboard.msg_score_info(name=obj.get("name"),
                                                                score=obj.get("score"),
                                                                team_mvp=obj.get("mvp"),
                                                                trend=obj.get("trend"),
                                                                country_flag=obj.get("country_flag"),
                                                                rank=obj.get("rank"),
                                                                first_blood_count=obj.get("fbc"),
                                                                id=obj.get("id"),
                                                                logo=obj.get("logo"))
            score_infos.append(scoreboard_info)
        scoreboard = sysctrl_scoreboard()
        scoreboard.score_info.MergeFrom(score_infos)
        return wrap_message(scoreboard)

    @staticmethod
    def mk_ui_chart_init(panel_id, chart_data):
        chart = ui_chart_init(panel_id=panel_id, data=chart_data)
        return wrap_message(chart)

    @staticmethod
    def mk_ui_chart_update(panel_id, chart_data):
        chart = ui_chart_update(panel_id=panel_id, data=chart_data)
        return wrap_message(chart)

