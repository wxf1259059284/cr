#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-8 下午1:49
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : linechart.py
# @Project : cpss

from sisdk.charts.chart import Chart

class LineChart(Chart):
    def __init__(self, chart_id, title, is_area=False):
        """
        初始化柱状图
        """
        super(LineChart, self).__init__(chart_id, title)
        self.max_slices = 30
        self.html_file = self.url_prefix + "line.html"
        self.series = {}
        self.legends = []
        self.xAxis = []
        if is_area:
            self.is_area = "1"
        else:
            self.is_area = "0"

    def add_slice(self, x_label, slice_data):
        """
        添加一个数据切片
        :param x_label: 如当前时刻10:10:01
        :param slice_data: 如流量[('红', 100),('蓝', 200)]
        """
        for sd in slice_data:
            if sd[0] not in self.series:
                self.series[sd[0]] = [sd[1]]
            else:
                self.series[sd[0]].append(sd[1])
                if len(self.series[sd[0]]) > self.max_slices:
                    self.series[sd[0]].pop(0)
            if sd[0] not in self.legends:
                self.legends.append(sd[0])
            self.xAxis.append(x_label)
            if len(self.xAxis) > self.max_slices:
                self.xAxis.pop(0)

    def to_dict(self):
        chart_data = {}
        series_data = []
        for key in self.series:
            series_data.append({"data": self.series[key], "name": key, 'type':'line'})
        chart_data['title'] = self.title
        chart_data['xAxis'] = self.xAxis
        chart_data['legend'] = self.legends
        chart_data['color'] = self.colors
        chart_data["area"] = self.is_area
        chart_data['data'] = series_data
        return chart_data


if __name__ == "__main__":
    import random
    line = LineChart("Line1")
    for i in range(0, 20):
        line.add_slice("K"+ str(i), [('红', random.randint(1,100)), ('蓝', random.randint(1,100))])
    line.to_json()