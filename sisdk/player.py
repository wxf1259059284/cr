#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-3 下午6:18
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : player.py.py
# @Project : cpss
import ctypes
import inspect
import time
import base64
import threading
import logging
import sisdk.libcr.enums as Enums
from .stores import StoreSQLite3, StoreDummy
from .libcr.atom_ui import AtomUi


def _async_raise(tid, exctype):
   tid = ctypes.c_long(tid)
   if not inspect.isclass(exctype):
      exctype = type(exctype)
   res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
   if res == 0:
      raise ValueError("invalid thread id")
   elif res != 1:
      ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
      raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
   _async_raise(thread.ident, SystemExit)



class VisPlayer(object):
    def __init__(self, channel_id="", db_type="sqlite3", db_conf={}, vis_obj=""):
        self.channel_id = channel_id
        self.vis = vis_obj
        self.play_speed = 1.0
        self.flag_stop = False
        self.flag_pause = False
        self.played_state = []
        self.stop_thread = False
        self.progress = 0
        if db_type == "sqlite3":
            self.store = StoreSQLite3(channel_id, db_conf.get("db_path"))
        else:
            self.store = StoreDummy()

    def get_state_seq(self, seq_uid="", timestamp=0):
        return self.store.get_state_seq(seq_uid, timestamp)

    def play_start(self):
        # 开始播放
        th_play = threading.Thread(name=self.channel_id, target=self.__do_start)
        th_play.setDaemon(True)
        th_play.start()
        while True:
            if self.stop_thread:
                logging.info("stop threading now!")
                stop_thread(th_play)
                th_play = threading.Thread(name=self.channel_id, target=self.__do_start, args=(self.progress,))
                th_play.setDaemon(True)
                th_play.start()
                self.stop_thread = False

    def play_stop(self):
        # 停止播放
        self.flag_stop = True
        ui_replay_message = AtomUi.mk_playback_progress(Enums.EnumProgressAction.play)
        self.vis.pub_message(ui_replay_message)

    def play_pause(self):
        # 暂停播放
        self.flag_pause = True
        ui_replay_message = AtomUi.mk_playback_progress(Enums.EnumProgressAction.play)
        self.vis.pub_message(ui_replay_message)

    def play_resume(self):
        # 恢复播放
        self.flag_pause = False

    def __do_start(self, index=0):
        cur, cnt_total = self.store.get_messages_iter()
        cnt_current = 1
        last_timestamp = 0
        if index:
            cnt_current = int(index * cnt_total)
            cur, _ = self.store.get_messages_iter(cnt_current)
        for data in cur:
            progress = float(cnt_current) / cnt_total
            logging.debug("Replay progress %.2f (%d/%d)" % (progress, cnt_current, cnt_total))
            if self.flag_stop:      # 停止播放直接跳出
                break
            if self.flag_pause:     # 暂停播放还能恢复
                ui_replay_message = AtomUi.mk_playback_progress(Enums.EnumProgressAction.pause, progress,
                                                                self.play_speed)
                self.vis.pub_message(ui_replay_message)
                while True:
                    if not self.flag_pause:
                        break
            else:
                ui_replay_message = AtomUi.mk_playback_progress(Enums.EnumProgressAction.play, progress,
                                                                self.play_speed)
                self.vis.pub_message(ui_replay_message)
            id, message_b64, timestamp, datetime = data
            message = base64.b64decode(message_b64)
            # 这里开始模型时间间隔进行回放
            if not last_timestamp == 0:
                time_interval = float(timestamp - last_timestamp)
                adjusted_interval = time_interval / self.play_speed
                # print cnt_current, adjusted_interval, "seconds to next action..."
                if not index:
                    time.sleep(adjusted_interval)
                index = None
            last_timestamp = timestamp
            self.vis.pub_message(message)
            # 把状态也存进redis 只能根据每条message的时间戳查询, TODO: 每轮查询一次，存储一次redis 更好解决
            seq_states = self.get_state_seq(timestamp=timestamp)
            for state in seq_states:
                self.vis.save_state(state.get("key"), state)
            cnt_current += 1
        cur.close()
        self.flag_stop = True
        logging.debug("Replay ended!")

    def get_store_state(self, var):
        cur, cnt_total = self.store.get_messages_iter()
        cnt_current = int(var * cnt_total)
        cur, _ = self.store.get_messages_iter(cnt_current)
        message_timestamp = cur.fetchone()[2]
        cur.close()
        states_got = self.get_state_seq(timestamp=message_timestamp)
        return states_got






