# -*- coding: utf-8 -*-
from channels import Channel

from base_evaluation.models import EvaluationReport, CheckReport
from base_evaluation.web.serializers import EvaluationReportSerializer, CheckReportSerializer


class EvaluationOperation(object):
    def __init__(self, data, filter_func=None):
        self.check_report = get_check_report(data)
        self.filter_func = filter_func
        self.evaluation = None

    def is_suit_report(self):
        # 按照传入的过滤方法判断数据是否符合过滤条件
        if self.filter_func and self.filter_func(self.check_report.result):
            return True
        else:
            return False

    def save_evaluation(self):
        # 根据传入的CheckReport存储对应EvaluationReport
        evaluation_data = {'report': self.check_report}
        self.evaluation = EvaluationReport.objects.create(**evaluation_data)

    def save_suit_evaluation(self):
        if self.is_suit_report():
            self.save_evaluation()
        else:
            pass

    def add_task_to_channel(self):
        self.save_suit_evaluation()
        if self.evaluation:
            data = EvaluationReportSerializer(self.evaluation).data
            self.add_data_to_channel(data)

    @classmethod
    def add_data_to_channel(cls, data):
        evaluation_msg = {
            'channel': 'evaluation',
            'content': data,
            'delay': 0 * 1000
        }
        Channel('asgi.delay').send(evaluation_msg)


def get_check_report(data):
    if isinstance(data, CheckReportSerializer):
        return data.instance
    elif isinstance(data, CheckReport):
        return data
    else:
        raise ValueError('Invalid CheckReport Data')
