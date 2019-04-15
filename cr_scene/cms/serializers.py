# -*- coding: utf-8 -*-
import json

from rest_framework import serializers

from base.utils.rest.serializers import ModelSerializer
from base_auth.models import User
from base_auth.cms.serializers import UserSerializer, OwnerSerializer
from base_mission.cms.serializers import MissionSerializer
from traffic_event.cms.serializers import TrafficEventSerializer
from base_scene.cms.serializers import SceneConfigSerializer
from base_scene.common.scene import SceneHandler

from cr_scene.models import CrScene, CrEvent, CrEventScene, MissionPeriod


class CrSceneSerializer(ModelSerializer):
    missions = MissionSerializer(many=True, read_only=True)
    traffic_events = TrafficEventSerializer(many=True, read_only=True)
    scene_config = SceneConfigSerializer(read_only=True)

    scene_data = serializers.SerializerMethodField()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('scene_config')
        queryset = queryset.prefetch_related(
            'missions',
            'traffic_events')

        return queryset

    def get_scene_data(self, obj):
        request = self.context.get('request')
        user = request.user if request else self.context.get('user')
        if obj.scene and user:
            handler = SceneHandler(user, scene=obj.scene)
            return handler.get()
        else:
            return None

    class Meta:
        model = CrScene
        fields = ('id', 'missions', 'traffic_events', 'name', 'scene_config', 'scene', 'roles', 'scene_data')
        read_only_fields = ('scene',)


class CrEventSceneSeriallizer(ModelSerializer):
    cr_scene_data = serializers.SerializerMethodField()
    roles_data = serializers.SerializerMethodField()

    cr_scene_instance_data = serializers.SerializerMethodField()

    def get_cr_scene_data(self, obj):
        return CrSceneSerializer(obj.cr_scene, fields=('id', 'name', 'roles')).data

    def get_roles_data(self, obj):
        try:
            role_users = json.loads(obj.roles)
            roles = json.loads(obj.cr_scene.roles)
            role_users_mapping = {role['role']: role for role in role_users}
            all_user_ids = []
            for role in roles:
                user_ids = role_users_mapping.get(role['value'], {}).get('users', [])
                all_user_ids.extend(user_ids)

            users = UserSerializer(User.objects.filter(pk__in=all_user_ids), many=True,
                                   fields=('id', 'logo', 'rep_name')).data
            id_user = {user['id']: user for user in users}
            for role in roles:
                user_ids = role_users_mapping.get(role['value'], {}).get('users', [])
                role['users'] = [id_user[user_id] for user_id in user_ids if user_id in id_user]
            return roles
        except Exception:
            return []

    def get_cr_scene_instance_data(self, obj):
        request = self.context.get('request')
        user = request.user if request else self.context.get('user')
        if obj.cr_scene_instance and user:
            handler = SceneHandler(user, scene=obj.cr_scene_instance)
            return handler.get()
        else:
            return None

    class Meta:
        model = CrEventScene
        fields = (
            'id', 'cr_event', 'cr_scene', 'name', 'roles', 'cr_scene_instance', 'extra', 'cr_scene_data', 'roles_data',
            'cr_scene_instance_data')


class CrEventSeriallizer(OwnerSerializer, ModelSerializer):
    cr_scenes = serializers.SerializerMethodField()

    def get_cr_scenes(self, obj):
        return CrEventSceneSeriallizer(CrEventScene.objects.filter(cr_event=obj), many=True).data

    class Meta:
        model = CrEvent
        fields = ('id', 'name', 'logo', 'description', 'cr_scenes', 'start_time', 'end_time', 'status')


class MissionPeriodSerializer(ModelSerializer):
    class Meta:
        model = MissionPeriod
        fields = '__all__'
