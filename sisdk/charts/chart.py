#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-2 上午10:18
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : chart.py.py
# @Project : cpss

import json
import datetime

class DefaultJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if hasattr(obj, 'config'):
            return obj.config


class Chart(object):
    """
    TODO:实现更多的细节控制，如颜色（序列）、图例
    """
    def __init__(self, chart_id, title):
        self.chart_id = chart_id
        self.title = title
        self.colors = ["#ff4546", "#009eff", "#2ec7c9", "#ffb980", "#b6a2de", "#00FF00"]
        #self.url_prefix = "localGame://echarts/"
        self.url_prefix =  "http://127.0.0.1:8050/static/charts/"

    def set_color(self, colors):
        self.colors = colors

    def to_dict(self):
        return {"WARNING":"to_dict() not implemented!"}

    def to_json(self):
        chart_data = self.to_dict()
        chart_json = json.dumps(chart_data, cls=DefaultJsonEncoder)
        return chart_json
