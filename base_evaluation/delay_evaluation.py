# -*- coding: utf-8 -*-
from base_auth.models import User
from .web import consumers as evaluation_consumers


def evaluation_push(message):
    if type(message) == dict:
        data = message
    else:
        data = message.content

    users = User.objects.all()
    for user in users:
        evaluation_consumers.EvaluationReportWebsocket.latest_evaluation_report(user, data)
