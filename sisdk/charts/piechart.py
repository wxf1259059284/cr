#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-2 上午10:23
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : piechart.py
# @Project : cpss
from sisdk.charts.chart import Chart


class PieChart(Chart):
    def __init__(self, chart_id, title):
        super(PieChart, self).__init__(chart_id, title)
        self.data_label = []
        self.data_value = []
        self.html_file = self.url_prefix + "pie.html"

    def fill(self, data_label, data_value):
        self.data_label = data_label
        self.data_value = data_value

    def to_dict(self):
        chart_data = {}
        series_data = []
        for idx, item in enumerate(self.data_value):
            series_item = {'value': item, 'name': self.data_label[idx]}
            series_data.append(series_item)
        chart_data['title'] = self.title
        chart_data['color'] = self.colors
        chart_data['data'] = series_data
        return chart_data


if __name__ == "__main__":
    attr = ["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"]
    v1 = [11, 12, 13, 10, 10, 10]
    pie = PieChart("饼图示例")
    pie.fill(attr, v1)
    pie.to_json()