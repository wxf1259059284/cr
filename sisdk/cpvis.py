#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-21 上午10:11
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : cpvis.py
# @Project : cpss

import json
import base64
import logging
import sys
import threading
import time

from sisdk.consts import CONST, WORLD_TYPE_REVERSE, WORLD_STATES, EnumRequestType
from sisdk.redisclients import ChannelPublisher, DataStore, ChannelSubscriber
from sisdk.recorder import VisRecorder
from sisdk.player import VisPlayer
from sisdk.messages import RequestMessageParser, ScoreboardMessage


def base64_encode(message):
    if sys.version > '3':
        return str(base64.b64encode(message), 'utf-8')
    else:
        return base64.b64encode(message)


def base64_decode(message):
    if sys.version > '3':
        # TODO: python3传过来的数据解析之后有乱码 ret = '	server-37'
        return str(base64.b64decode(message), 'utf-8')
    else:
        return base64.b64decode(message)


class SingleIdObject(object):
    """
    尝试性的实验了一个根据id只生成1个实例的类，如果有问题换掉。
    """
    __instances = {}                        # 用来保存所有的已生成的实例
    __instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # 根据args和kwargs生成实例标识（取第1个参数或id)
        if len(args) > 0:
            id_str = str(args[0])
        else:
            id_str = str(kwargs.get("id"))
        identity = "_instance_" + id_str
        if not identity in SingleIdObject.__instances:
            with SingleIdObject.__instance_lock:
                SingleIdObject.__instances[identity] = object.__new__(cls)
            return SingleIdObject.__instances[identity]
        else:
            logging.warning("Returned ALREADY-EXIST SingleIdObject(0x%x) instance with id=%s, your new params may not processed!" % (id(SingleIdObject.__instances[identity]), id_str))
            return SingleIdObject.__instances[identity]

    def destroy(self):
        identity = "_instance_" + str(self.id)
        del SingleIdObject.__instances[identity]

    def __repr__(self):
        str_repr = "<SingleIdObject object %s at 0x%x>" % (str(self.id), id(self))
        return str_repr


class CpVis(SingleIdObject):
    def __init__(self, world_type, world_id, event_title="", db_type="", db_conf={}, replay=False, redis_conf={}):
        """
        :param world_type: 用于区分OJ/AD/CR
        :param world_id: 唯一的ID，会和world_type组合成channel_id
        :param db_type: 用于录像/回放的数据库类型，目前只能是sqlite3
        :param db_conf: 数据库配置文件，目前只能填写{"db_path":"xxx"}
        :param replay: 是否用于回放的频道
        :param redis_conf: redis的配置{"host":"","port":"","password":""}
        """
        self.replay = replay
        if self.replay:
            self.channel_id = "%s_%s_REPLAY" % (WORLD_TYPE_REVERSE.get(world_type), str(world_id))
        else:
            self.channel_id = "%s_%s_LIVE" % (WORLD_TYPE_REVERSE.get(world_type), str(world_id))
        self.publisher = ChannelPublisher(self.channel_id, redis_conf)
        self.command_subscriber = ChannelSubscriber(listen_channel_id=self.channel_id+"_command",
                                                    callback_id=self.channel_id,
                                                    callback=self.on_command)
        self.command_subscriber.start_listen()
        self.state_store = DataStore(self.channel_id + "_saved", redis_conf)
        self.recorder = VisRecorder(self.channel_id, db_type, db_conf)
        # 这里往siserver发了一个指令，创建一个channel
        if replay:
            self.publisher.pub_request("CREATE_CHANNEL:%s" % self.channel_id + ":" + event_title)
            self.player = VisPlayer(self.channel_id, db_type, db_conf, self)
        else:
            self.publisher.pub_request("CREATE_CHANNEL:%s" % self.channel_id + ":" + event_title)
        self.scoreboard = ScoreboardMessage()

    def __repr__(self):
        return "<CpVis(%s) object at %x>" % (self.channel_id, id(self))

    def callback(self, vis_obj, channel_id, client_id, command):
        """
        客户端发生点击等事件后的回调函数，应当在业务中使用set_callback换用自己的处理函数以方便使用
        :param channel_id: 当前的channel_id
        :param client_id: 当前的客户端id
        :param command: 发来的指令
        """
        logging.info( "Command arrived, use set_callback to specify a processor.")

    def restore_countdown(self, var):
        logging.info("Restore countdown not implemented!!")

    def restore_current(self):
        logging.info("Restore current not implemented!!")

    def on_command(self, channel_id, client_id, command):
        """
        在callback之前，系统自动处理的一些指令在这里实现，包括客户端连接、客户端关闭等
        :param channel_id: 当前的channel_id
        :param client_id: 当前的客户端id
        :param command: 发来的指令
        """
        logging.debug("ON_COMMAND_RECV: channel_id [%s], client_id [%s], command [%s]" % (channel_id, str(client_id), str(command)))
        try:
            command = base64_decode(command)
        except Exception as e:
            logging.error("Error parsing base64 command" + str(e))
            command = ""
        if command == CONST.VIS_CLIENT_CONNECTED:
            self.restore_states()
        elif command == CONST.VIS_CLIENT_CLOSED:
            pass
        else:
            req_msg = RequestMessageParser.parse(command)
            # TODO:在这里把进度点击处理了，其它的交用户处理，但现在无法区别开是否为进度点击
            if req_msg:
                if req_msg.requestType == EnumRequestType.progress_click:
                    logging.info(" Request Progress messages will be processed by base class. ")
                    logging.info(req_msg.requestType, req_msg.id, req_msg.val)
                    self.jump_replay(req_msg.val)
                elif req_msg.requestType == EnumRequestType.progress_click_pause:
                    logging.info("TODO: Pause Clicked!!")
                    self.pause_replay()
                elif req_msg.requestType == EnumRequestType.progress_click_play:
                    logging.info("TODO: Play Clicked!!")
                    self.resume_replay()
                elif req_msg.requestType == EnumRequestType.progress_click_speed:
                    logging.info(req_msg.val)
                    logging.info(" Speed Clicked!!  ")
                    self.player.play_speed = req_msg.val
                else:
                    self.callback(self, channel_id, client_id, req_msg)

    def restore_states(self):
        """
        从状态存储里恢复状态并发送
        :return:
        """
        keys = self.state_store.keys()
        for key in keys:
            try:
                if not self.replay:
                    if key == 'TIME_SECONDS_COUNTDOWN':     # 还原倒计时
                        data = self.state_store.get(key)
                        data = json.loads(data)
                        saved_state = json.loads(data['value'])
                        saved_state['SECONDS'] = int(saved_state['SECONDS'] - (time.time() - saved_state['MOMENT']))
                        saved_state['MOMENT'] = time.time()
                        self.restore_countdown(saved_state)
                    elif key == 'TIME_CURRENT':    # 还原服务器时间
                        self.restore_current()
                    else:
                        data = self.state_store.get(key)
                        data = json.loads(data)
                        message = base64.b64decode(data['message'])
                        self.pub_message(message)
                else:
                    data = self.state_store.get(key)
                    data = json.loads(data)
                    message = base64.b64decode(data['message'])
                    self.pub_message(message)
            except Exception as e:
                logging.error(str(e))

    def retrieve_states(self):
        """
        从redis的状态缓存里获取状态数据列表
        """
        keys = self.state_store.keys()
        state_data = []
        for key in keys:
            try:
                data = self.state_store.get(str(key))
                if data:
                    data = json.loads(data)
                    state_data.append(data)
            except Exception as e:
                logging.error("Error retrieve state values:" + str(e))
        return state_data

    def set_callback(self, callback_func):
        """
        把命令处理函数设置为用户自定义的函数
        :param callback_func: 自定义函数
        """
        self.callback = callback_func
        logging.debug("Command callback set to: " + str(callback_func))

    def pub_message(self, message):
        """
        发布消息
        :param message: 序列化之后的二进制消息
        """
        try:
            self.publisher.pub_message(message)
            b64_message = base64_encode(message)
            if not self.replay:
                self.recorder.save_message(b64_message)
            return True, "message sent"
        except Exception as e:
            return False, str(e)

    def pub_state(self, state_name, state_value, message):
        """
        发布状态，和发布消息的区别是，状态会单独存储下来，客户端重连时会在on_command里处理
        :param state_name: 状态名
        :param state_value: 状态值（人工可读）
        :param message: 状态对应的消息（二进制）
        """
        try:
            self.publisher.pub_message(message)
            # b64_message = base64.b64encode(message)
            b64_message = base64_encode(message)
            state_value = json.dumps(state_value)
            stored_state = json.dumps({"key":state_name, "value": state_value, "message": b64_message})
            self.state_store.set(state_name, stored_state)
            if not self.replay:
                current_state = self.retrieve_states()
                self.recorder.save_message(b64_message) # 同时也存一条到数据流中
                self.recorder.save_state(current_state)
        except Exception as e:
            logging.error("pub_state error: %s" % str(e))
            raise

    def save_state(self, state_name, state_value):
        self.state_store.set(state_name, state_value)

    def load_state(self, state_name):
        return self.state_store.get(state_name)

    def load_state_from_replay_file(self, seq_uid):
        # 从数据库中获得状态（用于回放）
        seq_state = self.player.get_state_seq(seq_uid)
        for state in seq_state:
            self.save_state(state.get("key"), state)
        self.restore_states()

    def start_replay(self, speed=1.0):
        if self.player:
            self.player.play_speed = speed
            self.load_state_from_replay_file("FIRST")
            self.player.play_start()

    def jump_replay(self, var):
        if self.player:
            seq_state = self.player.get_store_state(var)
            for state in seq_state:
                self.save_state(state.get("key"), state)
            self.restore_states()
            self.player.stop_thread = True
            # self.player.play_start(var)
            self.player.progress = var

    def stop_replay(self):
        if self.player:
            self.player.play_stop()

    def pause_replay(self):
        if self.player:
            self.player.play_pause()

    def resume_replay(self):
        if self.player:
            self.player.play_resume()

    def refresh_scoreboard(self, scoreboard_title=""):
        """
        设置排行榜之后调用，更新排行榜
        :param scoreboard_title: 排行榜标题
        :return:
        """
        self.scoreboard.title = scoreboard_title
        self.scoreboard.sort()
        data = self.scoreboard.to_dict()
        msg = self.scoreboard.to_binary()
        self.pub_state(WORLD_STATES.SCOREBOARD, data, msg)
        logging.debug("Scoreboard data sended!")


