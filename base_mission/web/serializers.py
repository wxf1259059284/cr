# -*- coding: utf-8 -*-
from rest_framework import serializers

from base_mission import models as mission_models
from cr_scene import models as scene_models
from base_auth.models import User


class ExamTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = mission_models.ExamTask
        # fields = '__all__'
        exclude = ('answer',)


def get_extra_data(obj):
    if obj.examtask_set.all():
        return ExamTaskSerializer(obj.examtask_set.filter(status=1), many=True).data
    elif hasattr(obj, 'checkmission'):
        return CheckSerializer(getattr(obj, 'checkmission')).data
    elif hasattr(obj, 'ctfmission'):
        return CTFSerializer(getattr(obj, 'ctfmission')).data
    return ''


class MissionSerializer(serializers.ModelSerializer):
    create_user_name = serializers.SerializerMethodField()
    extra_data = serializers.SerializerMethodField()
    period_name = serializers.SerializerMethodField()

    def get_period_name(self, obj):
        per = obj.crscene_set.all().first().missionperiod_set.filter(period_index=(obj.period-1), status=1).first()
        if per:
            return per.period_name
        else:
            return ''

    def get_extra_data(self, obj):
        if obj.examtask_set.all():
            return ExamTaskSerializer(obj.examtask_set.filter(status=1), many=True).data
        elif hasattr(obj, 'checkmission'):
            return CheckSerializer(getattr(obj, 'checkmission')).data
        elif hasattr(obj, 'ctfmission'):
            return CTFSerializer(getattr(obj, 'ctfmission')).data
        return ''

    def get_create_user_name(self, obj):
        if obj.create_user:
            return obj.create_user.username
        return User.objects.filter(is_superuser=1).first().username

    class Meta:
        model = mission_models.Mission
        fields = "__all__"


class CTFSerializer(serializers.ModelSerializer):
    class Meta:
        model = mission_models.CTFMission
        fields = '__all__'


class CheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = mission_models.CheckMission
        fields = '__all__'


class CTFMissionSerializer(MissionSerializer):
    ctfmission = CTFSerializer()

    class Meta:
        model = mission_models.Mission
        fields = '__all__'


class CheckMissionSerializer(MissionSerializer):
    checkmission = CheckSerializer()

    class Meta:
        model = mission_models.Mission
        fields = '__all__'


class AgentCheckSerializer(MissionSerializer):
    class Meta:
        model = scene_models.MissionAgentUpload
        fields = '__all__'
