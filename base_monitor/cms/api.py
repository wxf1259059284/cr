# -*- coding: utf-8 -*-
from rest_framework.decorators import action
from rest_framework import viewsets, filters, status, exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base.utils.rest.mixins import DestroyModelMixin, CacheModelMixin, PMixin
from django.conf import settings

from base_monitor.cms.constant import ScriptType, Suffix
from base_monitor.cms.error import MonitorError
from . import serializers as monitor_serializers
from base_monitor import models as monitor_models
from . import constant

import os

SCRIPT_URL = os.path.join(settings.MEDIA_ROOT, 'scripts')


class MonitorCategoryViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = monitor_models.MonitorCategory.objects.all()
    serializer_class = monitor_serializers.MonitorCategorySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('cn_name', 'en_name')


class ScriptViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = monitor_models.Scripts.objects.all()
    serializer_class = monitor_serializers.ScriptsSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset

        script_type = self.request.query_params.get("type")
        if script_type is not None:
            if script_type not in [str(ScriptType.LOCAL), str(ScriptType.REMOTE)]:
                raise exceptions.ValidationError({'type': [MonitorError.ILLEGAL_PARAMETER]})
            queryset = queryset.filter(type=script_type)

        title = self.request.query_params.get('title', None)
        if title is not None:
            queryset = queryset.filter(title=title)

        suffix = self.request.query_params.get('suffix', None)
        if suffix is not None:
            if suffix not in [str(Suffix.PY), str(Suffix.SH)]:
                raise exceptions.ValidationError({'suffix': [MonitorError.ILLEGAL_PARAMETER]})
            queryset = queryset.filter(suffix=suffix)

        return queryset

    def sub_perform_create(self, serializer):
        super(ScriptViewSet, self).sub_perform_create(serializer)
        script = serializer.instance
        code = self.request.data.get('code', '')
        type = self.request.data.get("type")
        path = os.path.join(SCRIPT_URL, 'remote') if (int(type) == constant.ScriptType.REMOTE) else os.path.join(
            SCRIPT_URL, 'local')

        if os.path.exists(path):
            pass
        else:
            os.makedirs(path)

        file_path = get_file_path(script)
        with open(file_path, 'w') as file:
            file.write(code)

        serializer.save(
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )

        return True

    def sub_perform_update(self, serializer):
        script = serializer.instance
        request_path = get_file_path(self.request.data)
        exist_path = get_file_path(script)

        code = self.request.data.get('code')

        if code != script.code:
            with open(exist_path, 'w') as file:
                file.write(code)

        if request_path != exist_path:
            try:
                os.rename(exist_path, request_path)
            except Exception:
                pass

        serializer.save(
            last_edit_user=self.request.user,
        )
        super(ScriptViewSet, self).sub_perform_update(serializer)

        return True

    def sub_perform_destroy(self, instance):
        super(ScriptViewSet, self).sub_perform_destroy(instance)

        file_path = get_file_path(instance)

        try:
            os.remove(file_path)
        except Exception:
            pass

        return True

    def perform_batch_destroy(self, queryset):
        for instance in queryset:
            file_path = get_file_path(instance)
            try:
                os.remove(file_path)
            except Exception:
                pass
        if queryset.update(status=constant.Status.DELETE) > 0:
            return True
        return False

    @action(detail=False, methods=['post'])
    def check_title(self, request):
        title = self.request.query_params.get('title')
        suffix = self.request.query_params.get('suffix', constant.Suffix.PY)
        type = self.request.query_params.get("type", constant.ScriptType.REMOTE)
        script = self.queryset.filter(title=title, suffix=suffix, type=type, status=constant.Status.NORMAL)

        id = self.request.query_params.get("id")
        if id is not None:
            script = script.exclude(id=id)

        if script.exists():
            data = {"code": 'false'}
            return Response(status=status.HTTP_200_OK, data=data)
        else:
            data = {"code": 'true'}
            return Response(status=status.HTTP_200_OK, data=data)


def get_filename(data):
    if isinstance(data, dict):
        title = data.get("title", '')
        suffix = '.py' if (data.get("suffix") == constant.Suffix.PY) else '.sh'
        return title + suffix
    elif isinstance(data, monitor_models.Scripts):
        title = data.title
        suffix = '.py' if (data.suffix == constant.Suffix.PY) else '.sh'
        return title + suffix
    else:
        raise Exception("Wrong Data")


def get_file_path(data):
    if isinstance(data, dict):
        title = data.get("title", '')
        type = int(data.get("type", constant.ScriptType.REMOTE))
        suffix = '.py' if (data.get("suffix") == constant.Suffix.PY) else '.sh'
        directory = 'remote' if (type == constant.ScriptType.REMOTE) else 'local'
        return os.path.join(SCRIPT_URL, directory, title + suffix)

    elif isinstance(data, monitor_models.Scripts):
        title = data.title
        type = int(data.type)
        suffix = '.py' if (data.suffix == constant.Suffix.PY) else '.sh'
        directory = 'remote' if (type == constant.ScriptType.REMOTE) else 'local'
        return os.path.join(SCRIPT_URL, directory, title + suffix)
    else:
        raise Exception("Wrong Data")
