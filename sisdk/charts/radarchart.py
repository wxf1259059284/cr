#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-8 下午1:49
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : radarchart.py
# @Project : cpss


from sisdk.charts.chart import Chart

class RadarChart(Chart):
    def __init__(self, chart_id, title):
        """
        初始化雷达图
        """
        super(RadarChart, self).__init__(chart_id, title)
        self.legends = []
        self.indicators = {}
        self.html_file = self.url_prefix + "radar.html"
        self.series = {}

    def fill(self, series_name, series_data):
        self.series[series_name] = series_data

    def set_indicator(self, name, max):
        """
        存储雷达图的每个角名字，和边界
        :param name: 每个角的名字
        :param max: 最大边界
        :return:
        """
        self.indicators[name] = max

    def to_dict(self):
        chart_data = {}
        series_data = []
        for key in self.series:
            series_data.append({"value": self.series[key], "name": key})
        chart_data['title'] = self.title
        chart_data['legend'] = [key for key in self.series]
        chart_data['color'] = self.colors
        indicators_data = []
        for ikey in self.indicators:
            indicators_data.append({"name": ikey, "max": self.indicators[ikey]})
        chart_data['indicators'] = indicators_data
        chart_data['data'] = series_data
        return chart_data


if __name__ == "__main__":
    radar = RadarChart("Radar")
    for i in range(0,6):
        radar.set_indicator("I" + str(i), 100)
    radar.fill("red",  [5, 20, 36, 10, 75, 90])
    radar.fill("blue", [3, 10, 26, 8, 73, 50])
    radar.to_json()