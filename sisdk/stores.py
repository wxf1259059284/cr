#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-10-3 下午6:19
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : stores.py.py
# @Project : cpss

import sqlite3
import logging
import threading
import time
import json
from uuid import uuid4

class StoreDummy(object):
    def save_message(self, message):
        logging.warning("No recorder backend defined, data not recorded!")

    def save_state(self, state_values):
        logging.warning("No recorder backend defined, data not recorded!")

    def get_messages_iter(self, index=0):
        return [], 0

class StoreMySQL(object):
    pass

class StoreSQLite3(object):
    def __init__(self, channel_id, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)   #暂时关闭线程检查，不知道有没有问题,TODO:更靠谱的解决方案
        self.conn.execute('PRAGMA synchronous = OFF')
        self.channel_id = channel_id
        self.lock = threading.Lock()
        self.__create_init_tables()
        self.__save_meta()

    def __create_init_tables(self):
        sql = """CREATE TABLE IF NOT EXISTS %s_messages(id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                     message TEXT, 
                                                     timestamp FLOAT,
                                                     datetime DATETIME);""" % self.channel_id
        self.execute(sql)
        sql = """CREATE TABLE IF NOT EXISTS %s_states(id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                   seq_uid VARCHAR(50),
                                                   state_name VARCHAR(50), 
                                                   state_value TEXT, 
                                                   timestamp FLOAT,
                                                   state_message TEXT, datetime DATETIME);""" % self.channel_id
        self.execute(sql)
        sql = """CREATE INDEX IF NOT EXISTS IDX_%s_STATES_SEQ_UID ON 
                %s_states(seq_uid ASC)""" % (self.channel_id,self.channel_id)
        self.execute(sql)
        sql = """CREATE TABLE IF NOT EXISTS %s_state_seq(id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                                   seq_uid VARCHAR(50),
                                                   state_start_timestamp FLOAT,
                                                   state_end_timestamp FLOAT, 
                                                   update_timestamp FLOAT,
                                                   state_start_datetime DATETIME,
                                                   state_end_datetime DATETIME)""" % self.channel_id
        self.execute(sql)
        sql = """CREATE INDEX IF NOT EXISTS IDX_%s_state_start_timestamp ON 
              %s_state_seq(state_start_timestamp ASC)""" % (self.channel_id, self.channel_id)
        self.execute(sql)
        sql = """CREATE INDEX IF NOT EXISTS IDX_%s_state_end_timestamp ON 
            %s_state_seq(state_end_timestamp ASC)""" % (self.channel_id, self.channel_id)
        self.execute(sql)
        sql = """CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                  channel_id VARCHAR(50), 
                                                  create_datetime DATETIME,
                                                  update_datetime DATETIME)"""
        self.execute(sql)

    def __save_meta(self):
        local_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = """SELECT * FROM meta WHERE channel_id='%s'""" % self.channel_id
        cur = self.conn.execute(sql)
        rec = cur.fetchall()
        cur.close()
        if rec:
            sql = """UPDATE meta SET update_datetime = '%s'""" % local_datetime
        else:
            sql = """INSERT INTO meta (channel_id, create_datetime, update_datetime) 
                    VALUES ('%s', '%s', '%s')""" % (self.channel_id, local_datetime, local_datetime)
        self.execute(sql)

    def __save_single_state(self, seq_uid, state_name, state_value, state_message):
        timestamp = time.time()
        local_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = """INSERT INTO %s_states (seq_uid, state_name, state_value, state_message, timestamp, datetime) 
                VALUES ('%s', '%s', '%s', '%s', %.4f, '%s')""" % (
            self.channel_id, seq_uid, state_name, state_value, state_message, timestamp, local_datetime)
        self.execute(sql)

    def __get_states_by_seq_uid(self, seq_uid):
        states_out = []
        sql = "SELECT state_name,state_value,state_message FROM %s_states WHERE seq_uid='%s'" % (self.channel_id, seq_uid)
        states = self.fetchall(sql)
        for state in states:
            states_out.append({"key": state[0], "value": state[1], "message": state[2]})
        return states_out

    def commit(self):
        self.conn.commit()

    def execute(self, sql):
        try:
            # time1 = time.time()
            self.lock.acquire()
            self.conn.execute(sql)
            self.conn.commit()
            self.lock.release()
            # time2 = time.time()
            # print "Save SQL used:", time2-time1
        except Exception as e:
            logging.error(str(e))

    def fetchone(self, sql):
        cur = self.conn.execute(sql)
        data = cur.fetchone()
        cur.close()
        return data

    def fetchall(self, sql):
        cur = self.conn.execute(sql)
        data = cur.fetchall()
        cur.close()
        return data

    def save_message(self, message):
        timestamp = time.time()
        local_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = """INSERT INTO %s_messages (message, timestamp, datetime) 
                VALUES ('%s', %.4f, '%s')""" % (self.channel_id, message, timestamp, local_datetime)
        self.execute(sql)

    def save_state(self, state_values):
        timestamp = time.time()
        local_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        uuid = str(uuid4())
        # 找到上一条记录，更新其end_time
        sql_last_state = "SELECT * FROM %s_state_seq ORDER BY ID DESC LIMIT 1" % self.channel_id
        last_state = self.fetchone(sql_last_state)
        # 如果有上一条记录，把上一条记录的结束时间做一次更新
        if last_state:
            last_id = last_state[0]
            sql_update = """UPDATE %s_state_seq set state_end_timestamp=%.4f, update_timestamp=%.4f, state_end_datetime='%s'
                            WHERE id=%d""" % (self.channel_id, timestamp, timestamp, local_datetime, last_id)
            self.execute(sql_update)
        # 在状态序列表中保存一条新的
        sql_new = """INSERT INTO %s_state_seq (seq_uid, state_start_timestamp, state_end_timestamp, update_timestamp,
                            state_start_datetime) VALUES
                            ('%s', %.4f, %.4f, %.4f, '%s')""" % (self.channel_id, uuid,
                                                           timestamp, 0, timestamp, local_datetime)
        self.execute(sql_new)
        # 把各个状态存储到状态表中
        for single_state in state_values:
            self.__save_single_state(seq_uid=uuid,
                                     state_name=single_state.get("key"),
                                     state_value=json.dumps(single_state.get("value")),
                                     state_message=single_state.get("message"))

    def get_messages_iter(self, index=0):
        conn = sqlite3.connect(self.db_path)
        sql = "SELECT COUNT(*) FROM %s_messages" % self.channel_id
        cur = conn.execute(sql)
        cnt = cur.fetchone()
        if cnt:
            total_count = cnt[0]
        else:
            total_count = 0
        if not index:
            sql = "SELECT * FROM %s_messages" % self.channel_id
            cur = conn.execute(sql)
        else:
            # print index
            other_count = total_count - index
            sql = "SELECT * FROM %s_messages ORDER BY id LIMIT %s, %s" % (self.channel_id, index - 1, other_count)
            cur = conn.execute(sql)
        return cur, total_count

    def get_state_seq(self, seq_uid="", timestamp=0, timestring=""):
        """
        获取一个系列状态
        :param seq_uid: 可以为系列的UID，或者为FIRST、LAST指（数据库中）初始状态、（数据库中）最后的状态
        :param timestamp: 如果不为0，则通过timestamp查找到当时的状态
        :param timestring: 格式为2018-10-06 22:30:11，如果不为空，则通过这个字符串查到当时的状态
        :return:
        """
        states_got = []
        if seq_uid == "FIRST" and timestamp == 0:
            sql_first_state = "SELECT * FROM %s_state_seq ORDER BY ID LIMIT 1" % self.channel_id
            first_state = self.fetchone(sql_first_state)
            if first_state:
                first_state_uid = first_state[1]
                states_got = self.__get_states_by_seq_uid(first_state_uid)
        elif seq_uid == "LAST":
            pass
        else:
            if timestamp:
                sql_first_state = 'SELECT * FROM %s_states WHERE timestamp <= %s ORDER BY timestamp ' \
                                  'DESC limit 1;' % (self.channel_id, timestamp)
                first_state = self.fetchone(sql_first_state)
                if first_state:
                    first_state_uid = first_state[1]
                    states_got = self.__get_states_by_seq_uid(first_state_uid)

        return states_got