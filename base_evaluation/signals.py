# -*- coding: utf-8 -*-
from base_auth.models import User
from .filters import data_filter
from .web import serializers as evaluation_serializer, consumers as evaluation_consumers
from cr_scene.web.serializers import AgentSerializer
from base_evaluation.utils.evaluation_operations import EvaluationOperation

from threading import Thread


def record_synchronization(sender, instance=None, created=False, **kwargs):
    data = AgentSerializer(instance).data
    check_report = evaluation_serializer.CheckReportSerializer(data=data)
    check_report.is_valid(raise_exception=True)
    check_report.save()

    # todo:传递用户需要经过过滤
    users = User.objects.all()
    for user in users:
        evaluation_consumers.CheckReportWebsocket.latest_check_report(user, data)

    evaluation_operation = EvaluationOperation(check_report, data_filter.is_valid)
    trans = Thread(target=evaluation_operation.add_task_to_channel, args=())
    trans.setDaemon(True)
    trans.start()
