# -*- coding: utf-8 -*-
import re

from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator

from base_mission.constant import ScriptType, Suffix
from base_monitor import models as monitor_models
from base_monitor.cms.constant import REGEX
from base_monitor.cms.error import MonitorError
from base_scene.cms.serializers import StandardDeviceSerializer
from base.utils.rest.serializers import ModelSerializer


class MonitorCategorySerializer(ModelSerializer):
    class Meta:
        model = monitor_models.MonitorCategory
        fields = '__all__'
        extra_kwargs = {
            'en_name': {
                'min_length': 2, 'max_length': 100,
                'validators': [UniqueValidator(queryset=monitor_models.MonitorCategory.objects.all())]
            },

            'cn_name': {
                'min_length': 2, 'max_length': 100,
                'validators': [UniqueValidator(queryset=monitor_models.MonitorCategory.objects.all())]
            },
        }


class ScriptsSerializer(ModelSerializer):
    name = serializers.SerializerMethodField()
    create_user_name = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    category_cn_name = serializers.SerializerMethodField()
    category_en_name = serializers.SerializerMethodField()
    checker_name = serializers.SerializerMethodField()

    def get_category_cn_name(self, obj):
        if obj.category:
            return obj.category.cn_name
        return ''

    def get_category_en_name(self, obj):
        if obj.category:
            return obj.category.en_name
        return ''

    def get_name(self, obj):
        suffix = '.py' if (obj.suffix == 0) else '.sh'
        return obj.title + suffix

    def get_create_user_name(self, obj):
        if obj.create_user:
            return obj.create_user.username
        return ''

    def get_device(self, obj):
        return StandardDeviceSerializer(obj.checker).data

    def get_checker_name(self, obj):
        if obj.checker:
            return obj.checker.name
        return ''

    def validate(self, attrs):
        super(ScriptsSerializer, self).validate(attrs)

        if attrs.get("type") is None:
            raise exceptions.ValidationError({'type': [MonitorError.REQUIRED_FIELD]})
        else:
            if attrs.get("type") == ScriptType.REMOTE:
                if attrs.get("checker") is None:
                    raise exceptions.ValidationError({'checker': [MonitorError.REQUIRED_FIELD]})
            elif attrs.get("type") == ScriptType.LOCAL:
                if attrs.get("checker") is not None:
                    raise exceptions.ValidationError({'checker': [MonitorError.ILLEGAL_PARAMETER]})
            else:
                raise exceptions.ValidationError({'type': [MonitorError.ILLEGAL_PARAMETER]})

        if attrs.get('title') is None:
            raise exceptions.ValidationError({'title': [MonitorError.REQUIRED_FIELD]})
        else:
            title = attrs.get('title')
            if len(title) < 3 or len(title) > 100:
                raise exceptions.ValidationError({'title': [MonitorError.LENGTH_ERROR]})
            elif len(title.replace(' ', '')) != len(title):
                raise exceptions.ValidationError({'title': [MonitorError.TITLE_HAVE_SPACE]})
            elif re.match(unicode(REGEX.REGEX_TITLE), title) is None:
                raise exceptions.ValidationError({'title': [MonitorError.TITLE_ERROR]})
            else:
                if self.instance is None and monitor_models.Scripts.objects.filter(title=title,
                                                                                   type=attrs.get("type"),
                                                                                   suffix=attrs.get('suffix')).exists():
                    raise exceptions.ValidationError({'title': [MonitorError.TITLE_HAVE_EXISTED]})

        if attrs.get("suffix") is None:
            raise exceptions.ValidationError({'suffix': [MonitorError.TITLE_ERROR]})

        if attrs.get("code") is None:
            raise exceptions.ValidationError({'code': [MonitorError.REQUIRED_FIELD]})
        else:
            suffix = attrs.get("suffix")
            code = attrs.get("code")
            if suffix == Suffix.PY:
                if not ('checker' in code and 'fail' in code and 'success' in code):
                    raise exceptions.ValidationError({'code': [MonitorError.TLLEGAL_CODE]})
            elif suffix == Suffix.SH:
                if not ('CheckUp' in code and 'CheckDown' in code):
                    raise exceptions.ValidationError({'code': [MonitorError.TLLEGAL_CODE]})
            else:
                raise exceptions.ValidationError({'suffix': [MonitorError.ILLEGAL_PARAMETER]})

        return attrs

    class Meta:
        model = monitor_models.Scripts
        fields = '__all__'
