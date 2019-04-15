#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-2 上午10:29
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : barchart.py
# @Project : cpss

from sisdk.charts.chart import Chart

class BarChart(Chart):
    def __init__(self, chart_id, title, init_x_labels):
        """

        :param chart_id: 图表的id
        :param title: 图表上的标题
        :param init_x_labels: 数据标签
        """
        super(BarChart, self).__init__(chart_id, title)
        self.x_labels = init_x_labels
        self.html_file = self.url_prefix + "bar.html"
        self.series = {}

    def fill(self, series_id, series_data, x_labels=[]):
        self.series[series_id] = series_data
        if x_labels:
            self.x_labels = x_labels

    def to_dict(self):
        chart_data = {}
        series_data = []
        for key in self.series:
            series_data.append({"data": self.series[key], "type": "bar"})
        chart_data['title'] = self.title
        chart_data['x_labels'] = self.x_labels
        chart_data['legend'] = ["\u7ea2", "\u84dd"],
        chart_data['data'] = series_data
        chart_data['color'] = self.colors
        return chart_data


if __name__ == "__main__":
    bar = BarChart("我的第一个图表", ["阶段1","阶段2","阶段3","阶段4","阶段5","阶段6"])
    bar.fill("red",  [5, 20, 36, 10, 75, 90])
    bar.fill("blue", [3, 10, 26, 8, 73, 50])
    bar.to_json()