# -*- coding: utf-8 -*-
from base.utils.rest.mixins import CacheModelMixin, PublicModelMixin, PMixin, DestroyModelMixin
from rest_framework import filters, viewsets, permissions

from . import serializers as evaluation_serializer
from .. import models as evaluation_models
import datetime


class CheckReportViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = evaluation_models.CheckReport.objects.all()
    serializer_class = evaluation_serializer.CheckReportSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset

        timedelta = self.request.query_params.get('timedelta')
        if timedelta is not None:
            start_time = datetime.datetime.now() - datetime.timedelta(minutes=int(timedelta))
            queryset = queryset.filter(create_time__gte=start_time)

        cr_event_id = self.request.query_params.get('cr_event_id')
        if cr_event_id is not None:
            queryset = queryset.filter(cr_event_id=cr_event_id)

        return queryset

    def sub_perform_create(self, serializer):
        super(CheckReportViewSet, self).sub_perform_create(serializer)
        return True


class EvaluationReportViewSet(DestroyModelMixin, CacheModelMixin, PublicModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = evaluation_models.EvaluationReport.objects.all()
    serializer_class = evaluation_serializer.EvaluationReportSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)

    # ordering_fields = ('create_time',)
    # ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset

        timedelta = self.request.query_params.get('timedelta')
        if timedelta is not None:
            start_time = datetime.datetime.now() - datetime.timedelta(minutes=int(timedelta))
            queryset = queryset.filter(report__create_time__gte=start_time)

        cr_event_id = self.request.query_params.get('cr_event_id')
        if cr_event_id is not None:
            queryset = queryset.filter(report__cr_event_id=cr_event_id)

        return queryset

    def sub_perform_create(self, serializer):
        super(EvaluationReportViewSet, self).sub_perform_create(serializer)
        return True

    def sub_perform_update(self, serializer):
        serializer.save(evaluator=self.request.user)
        super(EvaluationReportViewSet, self).sub_perform_update(serializer)
        return True
