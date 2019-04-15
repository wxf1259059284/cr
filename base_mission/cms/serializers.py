# -*- coding: utf-8 -*-
import json
from rest_framework import serializers, exceptions

from base_mission import models as mission_models, constant
from base_auth.models import User
from base_mission.utils.handle_func import check_required_valid
from cr_scene.models import CrScene
from base_mission.constant import Type


class ExamTaskSerializer(serializers.ModelSerializer):
    def validate_task_title(self, data):
        if len(data) >= 20:
            raise exceptions.ValidationError('Task Title Should Be Less Than 20')
        return data

    def validate_task_type(self, data):
        if data not in constant.TopicProblem.values():
            raise exceptions.ValidationError('Invalid task_type')
        return data

    def validate(self, attrs):
        if attrs.get('task_type') != constant.TopicProblem.SHORTQUES:
            option = attrs.get('option')
            if not option:
                raise exceptions.ValidationError('option Required')

            options = json.loads(option)
            if type(options) != list:
                raise exceptions.ValidationError('option should be a list')

            for task_option in options:
                if task_option.keys() != ['optionLabel', 'optionValue']:
                    raise exceptions.ValidationError('Invalid option')

            ans_list = list(attrs.get('answer')) if (attrs.get('task_type') == constant.TopicProblem.MULTIPLE) else [
                attrs.get("answer")]
            label_list = [op.get('optionLabel') for op in options]
            for ans in ans_list:
                if ans not in label_list:
                    raise exceptions.ValidationError('Invalid answer')

        return attrs

    class Meta:
        model = mission_models.ExamTask
        fields = '__all__'


class MissionSerializer(serializers.ModelSerializer):
    create_user_name = serializers.SerializerMethodField()
    extra_data = serializers.SerializerMethodField()
    period_name = serializers.SerializerMethodField()

    def get_period_name(self, obj):
        try:
            per = obj.crscene_set.all().first().missionperiod_set.filter(period_index=(obj.period - 1),
                                                                         status=1).first()
            if per:
                return per.period_name
            else:
                return ''
        except Exception:
            return ''

    def create(self, validated_data):
        if validated_data['type'] == mission_models.Mission.Type.CHECK:
            # checker 默认发布
            validated_data['public'] = True
        return super(MissionSerializer, self).create(validated_data)

    def get_extra_data(self, obj):
        if obj.type == Type.EXAM:
            return ExamTaskSerializer(obj.examtask_set.filter(status=1), many=True).data
        elif obj.type == Type.CHECK:
            return CheckSerializer(getattr(obj, 'checkmission')).data
        elif obj.type == Type.CTF:
            return CTFSerializer(getattr(obj, 'ctfmission')).data
        return ''

    def get_create_user_name(self, obj):
        if obj.create_user:
            return obj.create_user.username
        return User.objects.filter(is_superuser=1).first().username

    def validate_title(self, data):
        if len(data) >= 20:
            raise exceptions.ValidationError('Mission Title Should Be Less Than 20')
        return data

    def validate_type(self, data):
        if data not in constant.Type.values():
            raise exceptions.ValidationError('Invalid Mission Type')
        return data

    def validate_difficulty(self, data):
        if data not in constant.Difficulty.values():
            raise exceptions.ValidationError('Invalid Mission Difficulty')
        return data

    def validate(self, attrs):
        super(MissionSerializer, self).validate(attrs)
        if not self.partial:
            data = self.initial_data
            exist_missions = CrScene.objects.get(id=data.get('cr_scene_id')).missions.all()
            title = data.get('title')
            if exist_missions.filter(title=title).exists():
                raise exceptions.ValidationError('Title Already Exists')
        return attrs

    class Meta:
        model = mission_models.Mission
        fields = "__all__"


class CTFSerializer(serializers.ModelSerializer):
    class Meta:
        model = mission_models.CTFMission
        fields = '__all__'


class CheckSerializer(serializers.ModelSerializer):
    def validate_check_type(self, data):
        if data not in constant.CheckType.values():
            raise exceptions.ValidationError('Invalid check_type')
        return data

    def validate(self, attrs):
        if attrs.get('check_type') == constant.CheckType.SYSTEM:
            required_fields = ['target_net', 'checker_id']
            check_required_valid(data=attrs, required_fields=required_fields)
        return attrs

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
