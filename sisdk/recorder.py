#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @date: 2018/10/3 10:32
# @name: recorder.py
# @author：Ivan Wang

import logging
from .stores import StoreSQLite3, StoreDummy

class VisRecorder(object):
    def __init__(self, channel_id="", db_type="sqlite3", db_conf={}):
        channel_id = channel_id.replace("LIVE", "REPLAY")
        if db_type == "sqlite3":
            self.store = StoreSQLite3(channel_id, db_conf.get("db_path"))
        else:
            self.store = StoreDummy()

    def save_message(self, message):
        # 存储消息
        #logging.debug("Message saved.")
        self.store.save_message(message)

    def save_state(self, state_values):
        # 每当有状态变化时做记录，应该记一个全量，每次回放跳的时候，直接发过去。
        # 但需要注意的是，类似Init_topo这种数据，不需要发送两次。应此有可能区分出3种类型：message, init_message, state_message
        #logging.debug("State Saved.")
        self.store.save_state(state_values)

if __name__ == "__main__":
    vr = VisRecorder("AD_1_LIVE", "sqlite3", {"db_path":"/devdata/tests/test_rec.db"})