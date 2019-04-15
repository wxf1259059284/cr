#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-9-22 下午7:15
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : messages.py.py
# @Project : cpss
import logging
import sys
import time

from sisdk.libcr.base_pb2 import sequence_message, atom_message, req_click, scoreboard
# from sisdk.libcr.cr_sysctrl_pb2 import sysctrl_scoreboard
from sisdk.libcr.enums import EnumMessageType, EnumScenarioType, EnumTrend
from google.protobuf.json_format import MessageToJson,MessageToDict

class SequenceMessageMaker(object):
    """
    用来生成指令队列（sequence_message）的类
    """
    def __init__(self, message_type=EnumMessageType.behavior, scenario_type=EnumScenarioType.all_scenarios):
        """
        初始化时，指定指令队列适用的场景类型
        :param scenario_type: 场景类型
        """
        self.instance = sequence_message()
        self.instance.header.id = str(time.time() * 1000)
        self.instance.header.timestamp = int(time.time() * 1000)
        self.instance.header.server = "127.0.0.1"
        self.instance.header.channel = "6"
        self.instance.header.type = message_type
        self.atoms = []

    def add_fragment(self, frag_message, wait=0):
        """
        处理一个消息片段，并将其包装成一个原子消息加入队列
        :param frag_message: 消息片段对象
        """
        atom = atom_message()
        atom.meta.cls = frag_message.__class__.__name__
        atom.meta.wait = wait
        atom.content.Pack(frag_message)
        self.atoms.append(atom)
        #self.instance.body.MergeFrom([atom])

    def to_binary(self):
        """
        转为二进制数据
        """
        # MergeFrom在一些版本的proto出错，先用extend试试
        # self.instance.body.MergeFrom(self.atoms)
        self.instance.body.extend(self.atoms)
        msg_data = self.instance.SerializeToString()
        return msg_data

    def to_json(self):
        """
        转为json
        """
        self.instance.body.extend(self.atoms)
        json_data = MessageToJson(self.instance)
        return json_data

    def to_dict(self):
        """
        转为dict
        """
        self.instance.body.extend(self.atoms)
        json_data = MessageToDict(self.instance)
        return json_data


    def serialized(self):
        return self.to_binary()

class RequestMessageParser(object):
    """
    解析消息队列
    """
    @staticmethod
    def parse(data):
        try:
            req_msg = req_click()
            if sys.version > '3':
                data = bytes(data, encoding="utf8")
                req_msg.ParseFromString(data)
            else:
                req_msg.ParseFromString(data)
            return req_msg
        except Exception as e:
            logging.error("Error msg %s" % e)
            return None

class ScoreboardMessage(object):
    def __init__(self, title=""):
        self.title = title
        self.entries = []

    def add_entry(self, id, name, score, logo="",
                  most_valuable_player="", trend=EnumTrend.still,
                  country_flag_url="", first_blood_count=0):
        """
        设置排行榜
        :param id: 队伍id
        :param name: 队伍名字
        :param score: 队伍分数
        :param logo: 队伍logo
        :param most_valuable_player: 最有价值选手
        :param trend: 分数趋势
        :param country_flag_url:
        :param first_blood_count: 一血次数
        :return:
        """
        entry_dict = {"id": str(id),
                      "name": name,
                      "score": score,
                      "most_valuable_player": most_valuable_player,
                      "trend": trend,
                      "country_flag": country_flag_url,
                      "rank": 0,
                      "first_blood_count": first_blood_count,
                      "logo": logo}
        existed_entry = False
        for entry in self.entries:
            if entry["id"] == str(id):
                entry.update(entry_dict)
                existed_entry = True
        if not existed_entry:
            self.entries.append(entry_dict)

    def sort(self):
        self.entries = sorted(self.entries, key=lambda keys: keys['score'], reverse=True)
        # 更新排名数字
        for idx, entry in enumerate(self.entries):
            self.entries[idx]["rank"] = idx + 1
    def to_dict(self):
        return self.entries

    def to_binary(self):
        score_infos = []
        for entry in self.entries:
            scoreboard_info = scoreboard.msg_score_info(name=entry.get("name"),
                                                        score=entry.get("score"),
                                                        team_mvp=entry.get("most_valuable_player"),
                                                        trend=entry.get("trend"),
                                                        country_flag=entry.get("country_flag"),
                                                        rank=entry.get("rank"),
                                                        first_blood_count=entry.get("first_blood_count"),
                                                        id=entry.get("id"),
                                                        logo=entry.get("logo"))
            score_infos.append(scoreboard_info)
        scoreboard_msg = scoreboard(title=self.title)
        scoreboard_msg.score_info.extend(score_infos)
        return wrap_message(scoreboard_msg)




def wrap_message(message):
    smq = SequenceMessageMaker(EnumMessageType.command, EnumScenarioType.all_scenarios)
    smq.add_fragment(message)
    return smq.serialized()

def get_sequece_message_maker():
    smq = SequenceMessageMaker(EnumMessageType.command, EnumScenarioType.all_scenarios)
    return smq