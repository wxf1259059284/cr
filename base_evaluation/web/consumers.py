# -*- coding: utf-8 -*-
from base_auth.cms.consumers import UserWebsocket
from base.utils.enum import Enum

from .. import models as evaluation_models
from . import serializers as evaluation_serializer

from datetime import datetime, timedelta


class CheckReportWebsocket(UserWebsocket):
    Event = Enum(
        LATEST_REPORT=1,
        ALL_REPORTS=2,
    )

    def receive(self, content, **kwargs):
        message = self.message
        if not message.user.is_authenticated:
            message.reply_channel.send({"close": True})
            return

        if content:
            event_id = content
            self.all_check_reports(message.user, event_id)

    @classmethod
    def _get_all_check_report(cls, cr_event):
        start_time = datetime.now() - timedelta(hours=1)
        reports = evaluation_models.CheckReport.objects.filter(cr_event_id=cr_event, create_time__gte=start_time)
        data = evaluation_serializer.CheckReportSerializer(reports, many=True).data
        return data

    @classmethod
    def all_check_reports(cls, user, cr_event):
        data = cls._get_all_check_report(cr_event)
        cls.user_send(user, data, code=cls.Event.ALL_REPORTS)

    @classmethod
    def latest_check_report(cls, user, data):
        cls.user_send(user, data, code=cls.Event.LATEST_REPORT)


class EvaluationReportWebsocket(UserWebsocket):
    Event = Enum(
        LATEST_EVALUATION=1,
        ALL_EVALUATIONS=2,
    )

    def receive(self, content, **kwargs):
        message = self.message
        if not message.user.is_authenticated:
            message.reply_channel.send({"close": True})
            return

        if content:
            event_id = content
            self.all_evaluation_reports(message.user, event_id)

    @classmethod
    def _get_all_evaluation_reports(cls, cr_event):
        start_time = datetime.now() - timedelta(hours=1)
        evaluations = evaluation_models.EvaluationReport.objects.filter(report__cr_event_id=cr_event,
                                                                        report__create_time__gte=start_time)
        data = evaluation_serializer.EvaluationReportSerializer(evaluations, many=True).data
        return data

    @classmethod
    def all_evaluation_reports(cls, user, cr_event):
        data = cls._get_all_evaluation_reports(cr_event)
        cls.user_send(user, data, code=cls.Event.ALL_EVALUATIONS)

    @classmethod
    def latest_evaluation_report(cls, user, data):
        cls.user_send(user, data, code=cls.Event.LATEST_EVALUATION)
