#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-21 上午10:01
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : redisclients.py
# @Project : cpss

import redis
import logging
import json
import base64
import threading
from .consts import CONST


class RedisBase(object):
    pool = None
    pool_ready = False

    def __init__(self, redis_conf={}, db=0):
        host = redis_conf.get("host", "127.0.0.1")
        port = redis_conf.get("port", 6379)
        password = redis_conf.get("password", "")
        if not RedisBase.pool_ready:
            RedisBase.pool = redis.ConnectionPool(host=host, port=port, password=password)
            RedisBase.pool_ready = True
            logging.info("Redis pool created!")
        self.r = redis.StrictRedis(connection_pool=RedisBase.pool, db=db)


class DataStore(RedisBase):
    """
    存储数据用
    """
    def __init__(self, channel_id, redis_conf={}):
        super(DataStore, self).__init__(redis_conf, db=CONST.REDIS_DB_STORE)
        self.channel_id = channel_id
        #TODO:这里对本频道的数据做了清除处理，应当确保同一个频道不会被初始化两次！
        self.clear()

    def set(self, key, value):
        this_key = self.channel_id + "_" + key
        if not isinstance(value, str):
            value = json.dumps(value)
        return self.r.set(this_key, value)

    def set_series(self, series_name, seq_no, key, value):
        self.set(str(series_name) + ":" + str(key) + ":" + str(seq_no), value)

    def get(self, key, default=None):
        this_key = self.channel_id + "_" + key
        ret = self.r.get(this_key)
        if not ret:
            ret = default
        return ret

    def get_series(self, series_name):
        key_pattern = self.channel_id + "_" + series_name +":*"
        key_prefix = self.channel_id + "_"
        data = [self.get(key.replace(key_prefix,"")) for key in self.r.scan_iter(key_pattern)]
        return data

    def keys(self):
        keys = []
        key_pattern = self.channel_id + "_*"
        key_prefix = self.channel_id + "_"
        for key in self.r.scan_iter(key_pattern):
            import sys
            if sys.version > '3':
                keys.append(str(key, 'utf-8').replace(key_prefix, ""))
            else:
                keys.append(key.replace(key_prefix, ""))

        return keys

    def clear(self):
        try:
            prefix = self.channel_id + "_*"
            for key in self.r.scan_iter(prefix):
                self.r.delete(key)
        except Exception as e:
            logging.error("Redis operation error:" + str(e))
            if "10061" in str(e):
                logging.error("Check you redis server status, and restart siserver!")
                exit()


class ChannelPublisher(RedisBase):
    """
    消息发布基类
    """

    def __init__(self, channel_id, redis_conf={}):
        super(ChannelPublisher, self).__init__(redis_conf, db=CONST.REDIS_DB_MQ)
        self.channel_id = channel_id
        self.ds = DataStore(channel_id, redis_conf)
        self.series_seed = {}

    def marshal_message(self, message):
        return message

    def pub_message(self, message):
        """
        发送普通消息
        """
        message = self.marshal_message(message)
        return self.r.publish(self.channel_id, message)

    def pub_state(self, state_name, message):
        """
        发送需要保存状态的（如地图、倒计时等信息）消息
        """
        message = self.marshal_message(message)
        pubr = self.r.publish(self.channel_id, message)
        setr = self.ds.set("STATE_" + state_name, message)
        if pubr and setr:
            return True
        else:
            return False

    def pub_series_state(self, series_name, state_name, message):
        """
        发送需要保存系列状态的（如题目）消息
        """
        seq_no = self.series_seed.get(series_name, 1)
        self.series_seed[series_name] = seq_no + 1
        message = self.marshal_message(message)
        pubr = self.r.publish(self.channel_id, message)
        setr = self.ds.set_series("STATE_" + series_name, seq_no, state_name, message)
        if pubr and setr:
            return True
        else:
            return False

    def pub_command(self, command):
        """
        发送3D客户端发来的指令，这些指令将由sdk来处理，3d客户端不处理
        """
        try:
            command_channel_id = self.channel_id + "_command"
            command['command'] = str(base64.b64encode(command['command']), 'utf-8')
            command = json.dumps(command)
            message = self.marshal_message(command)
            return self.r.publish(command_channel_id, message)
        except Exception as e:
            logging.error(str(e))
            logging.error(command)

    def pub_request(self, request):
        """
        发送给siserver的请求，如创建一个频道等
        """
        request_channel_id = CONST.REQUEST_CHANNEL
        request = json.dumps(request)
        message = self.marshal_message(request)
        return self.r.publish(request_channel_id, message)


class ChannelSubscriber(RedisBase):
    """docstring for ChannelHandler"""
    def __init__(self, listen_channel_id, callback_id, callback, redis_conf={}):
        super(ChannelSubscriber, self).__init__(redis_conf, db=CONST.REDIS_DB_MQ)
        self.callback_id = callback_id
        self.listen_channel_id = listen_channel_id
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(self.listen_channel_id)
        self.callback = callback
        self.make_stop = False

    def start_listen(self):
        self.listen_t = threading.Thread(name=self.__class__.__name__, target=self.do_listen)
        self.listen_t.setDaemon(True)
        self.listen_t.start()

    def do_listen(self):
        self.make_stop = False
        logging.info("Subscriber [%s] started" % self.listen_channel_id)
        for item in self.pubsub.listen():
            if self.make_stop:
                break
            try:
                data = item['data']
                if data != 1:   # 初次连接时会收到一个1,不知道为啥
                    transformed = self.transform_data(data)
                    client_id = transformed['client_id']
                    command = transformed['command']
                    self.callback(self.callback_id, client_id, command)
            except Exception as e:
                logging.error(str(e))
        logging.debug("Command Subscriber ended.")

    def stop_listen(self):
        self.pubsub.close()
        self.make_stop = True
        logging.info("subscriber stopped")

    def transform_data(self, data):
        try:
            data = json.loads(data)
        except Exception as e:
            data = data
        if not isinstance(data, dict):
            data = {"client_id": "", "command": data}
        else:
            if "client_id" not in data:
                data['client_id'] = ""
        return data
