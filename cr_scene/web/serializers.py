# -*- coding: utf-8 -*-
import logging
import os

import six
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework import serializers

from base.utils.rest.serializers import ModelSerializer
from base_auth.web.serializers import UserSerializer
from base_scene.common.scene import SceneHandler
from cr_scene import app_settings
from cr_scene import models as scene_models
from cr_scene.cms import serializers as cms_serializers
from cr_scene.error import error
from cr_scene.utils import common
from cr_scene.utils import validators as utils_validators

logger = logging.getLogger(__name__)


class CrSceneSerializer(cms_serializers.CrSceneSerializer):
    class Meta:
        model = scene_models.CrScene
        fields = ('id', 'missions', 'traffic_events', 'name', 'scene_config', 'roles')


class CrSceneModelSerializer(ModelSerializer):
    class Meta:
        model = scene_models.CrScene
        fields = "__all__"


class CrEventSerializers(cms_serializers.CrEventSeriallizer):
    event_count = serializers.SerializerMethodField()
    cr_scenes = serializers.SerializerMethodField()

    def _filter_data(self, key, obj=None):
        filter_data = {}
        if obj is not None:
            filter_data.update({"cr_event": obj})

        if self.context.get("request", None) is not None and \
                self.context['request'].data.get('_permission_scene_ids', None) is not None:
            filter_data.update({key: self.context['request'].data.get('_permission_scene_ids')})
        return filter_data

    def _filter_visconfig(self, nodes):
        data = []
        for node in nodes:
            if not node['id'].startswith('server'):
                continue
            if 'data' in node and node['data']['visible'] is True:
                data.append(node)
        logger.info('this cr scene nodes count is ==> {}'.format(len(data)))
        return data

    def get_cr_scenes(self, obj):
        filter_data = self._filter_data('cr_scene_id__in', obj)
        event_scenes = scene_models.CrEventScene.objects.filter(**filter_data)
        request = self.context.get('request')
        user = request.user if request else self.context.get('user')
        if user and app_settings.CHECKER_ONE_AS_ADMIN is False:
            event_scenes = [event_scene for event_scene in event_scenes if
                            common.can_role_get_scene(user.id, event_scene)]
        event_scenes_queryset = CrEventSceneSeriallizer.setup_eager_loading(event_scenes)
        return CrEventSceneSeriallizer(event_scenes_queryset, many=True).data

    def get_event_count(self, obj):
        machine_count_dict = {}
        missions_count = 0
        period_count = []
        filter_data = self._filter_data('id__in')
        setup_eager_loading_queryset = CrSceneSerializer.setup_eager_loading(obj.cr_scenes.filter(**filter_data))
        datas = CrSceneSerializer(setup_eager_loading_queryset, many=True,
                                  fields=('id', 'scene_config', 'missions')).data

        for data in datas:
            missions_count += len(data['missions'])
            tmp_mission = [mission['period'] for mission in data['missions']]
            period_count.extend(tmp_mission)
            vis_config = data['scene_config']['vis_config']
            if vis_config is None:
                logger.info('in this CrEventSerializers, we not get vis_config ==> {}'.format(vis_config))
            else:
                machine_count_dict[data['id']] = len(self._filter_visconfig(vis_config['nodes']))
        machine_count = sum(machine_count_dict.values())
        return {"machine_count": machine_count,
                "missions_count": missions_count,
                "period_count": len(set(period_count)),
                "machine_each_count": machine_count_dict,
                }

    def to_internal_value(self, data):
        logo = data.get('logo')
        default_logo = None

        if logo and isinstance(logo, (six.string_types, six.text_type)):
            default_logo_path = os.path.join(app_settings.FULL_DEFAULT_EVENT_LOGO_DIR, logo)
            if os.path.exists(default_logo_path):
                data._mutable = True
                default_logo = logo
                data.pop('logo')
                data._mutable = False
        ret = super(CrEventSerializers, self).to_internal_value(data)

        if default_logo:
            ret['logo'] = os.path.join(app_settings.DEFAULT_EVENT_LOGO_DIR, default_logo)
        cr_scenes = data.get('cr_scenes', None)

        if cr_scenes:
            ret['cr_scenes'] = cr_scenes
        return ret

    def validate(self, attrs):
        """验证多个字段联合验证"""
        if self.partial:
            start_time = attrs.get('start_time', self.instance.start_time)
            end_time = attrs.get('end_time', self.instance.end_time)
        else:
            start_time = attrs['start_time']
            end_time = attrs['end_time']

        if start_time >= end_time:
            raise exceptions.ValidationError(error.START_TIME_IS_GREATER_THAN_END_TIME)

        if 'cr_scenes' in attrs:
            if attrs['cr_scenes'] == '[]':
                raise exceptions.ValidationError(error.SELECT_AT_LEAST_ONE_SCENE)
            del attrs['cr_scenes']

        if 'logo' in attrs:
            if attrs['logo'] is None:
                raise exceptions.ValidationError(error.LOGO_CAN_NOT_BE_EMPTY)
        return attrs

    class Meta:
        model = scene_models.CrEvent
        fields = ('id', 'name', 'logo', 'description', 'cr_scenes', 'start_time', 'end_time', 'status', 'event_count')
        extra_kwargs = {
            'description': {'validators': [utils_validators.script_validator, ]},
            'name': {'max_length': 20,
                     'error_messages': {"max_length": _('x_field_length_cannot_exceed').format(length=20)}},
        }


class CrEventSceneSeriallizer(cms_serializers.CrEventSceneSeriallizer):
    cr_scene = CrSceneSerializer(read_only=True, fields=('id', 'name', 'scene_config', 'roles'))
    cr_scene_id = serializers.SerializerMethodField()

    def get_cr_scene_id(self, obj):
        return obj.cr_scene_id

    def get_cr_scene_instance_data(self, obj):
        request = self.context.get('request')
        user = request.user if request else self.context.get('user')
        if obj.cr_scene_instance and user:
            handler = SceneHandler(user, scene=obj.cr_scene_instance)

            main = request.query_params.get('main') if request else None
            if main and main.isdigit():
                main = int(main)

            if (not main or main == obj.pk) and common.can_role_get_scene(user.id, obj):
                fields_config = common.get_role_scene_fields_config(user.id, obj)
                data = handler.get(fields=fields_config)
            else:
                data = handler.get()
                common.filter_public_nodes(data)
                fields_config = common.get_role_scene_fields_config(user.id, obj, public=True)
                common.filter_scene_data_fields(data, fields=fields_config)

            return data
        else:
            return None

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            'cr_scene')
        return queryset

    class Meta:
        model = scene_models.CrEventScene
        fields = (
            'id', 'cr_event', 'cr_scene', 'name', 'roles', 'cr_scene_instance', 'extra', 'cr_scene_data', 'roles_data',
            'cr_scene_instance_data', 'cr_scene_id')


class CrEventSerializersList(ModelSerializer):
    cr_scenes = CrSceneSerializer(many=True, fields=('id', 'name', 'roles', 'scene_config'))
    creventscene_crevent = CrEventSceneSeriallizer(many=True, fields=('cr_scene_id', 'roles_data',))

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            'cr_scenes',
            'cr_scenes__scene_config',
            'creventscene_crevent',
        )

        return queryset

    class Meta:
        model = scene_models.CrEvent
        fields = (
            'id', 'logo', 'name', 'user', 'description', 'start_time', 'end_time', 'cr_scenes', 'creventscene_crevent')


class CrEventDetailSerializers(ModelSerializer):
    cr_event_scenes = serializers.SerializerMethodField()

    def get_cr_event_scenes(self, obj):
        request = self.context['request']
        event_scenes = scene_models.CrEventScene.objects.filter(cr_event=obj)
        # 普通学员页面不需要显示实例的给个拓扑
        cr_scene_id = request.data.get('cr_scene_id', None)
        if cr_scene_id:
            event_scenes = event_scenes.filter(cr_scene_id=cr_scene_id)

        # event_scenes = [event_scene for event_scene in event_scenes if
        #                 common.can_role_get_scene(request.user.id, event_scene)]
        data = []
        for event_scene in event_scenes:
            if app_settings.CHECKER_ONE_AS_ADMIN:
                data.append(CrEventSceneSeriallizer(event_scene, context={'request': request}).data)
                continue
            if common.can_role_get_scene(request.user.id, event_scene):
                data.append(CrEventSceneSeriallizer(event_scene, context={'request': request}).data)
            else:
                data.append(
                    CrEventSceneSeriallizer(event_scene, fields=('id', 'name', 'cr_scene_instance_data', 'extra'),
                                            context={'request': request}).data)
        return data

    class Meta:
        model = scene_models.CrEvent
        fields = ('id', 'start_time', 'end_time', 'name', 'cr_event_scenes', 'logo', 'description')


class EventNoticeSerializer(ModelSerializer):
    class Meta:
        model = scene_models.EventNotice
        fields = ('id', 'cr_event', 'notice', 'create_time', 'is_topped')


class AgentSerializer(ModelSerializer):
    class Meta:
        model = scene_models.MissionAgentUpload
        fields = '__all__'


class CrEventUserStandardDeviceSerializer(ModelSerializer):
    user = UserSerializer(read_only=True, fields=('id', 'rep_name'))

    class Meta:
        model = scene_models.CrEventUserStandardDevice
        exclude = ('modify_user',)
        read_only_fields = ('user',)


class CrSceneEventUserAnswerSerializer(ModelSerializer):

    def validate_score(self, value):
        if value < 0:
            raise exceptions.ValidationError(error.SUBMIT_SCORE_MUST_BE_GREATER_THAN_0)
        return value

    class Meta:
        model = scene_models.CrSceneEventUserAnswer
        fields = "__all__"


class ActivityReportSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        crsceneevent_usersubmitlogs = self.context.get('crsceneevent_usersubmitlogs', None)
        cr_scene_id_mapping = self.context.get('cr_scene_id_mapping', None)
        obj_data = self.context.get('obj_data', None)
        if crsceneevent_usersubmitlogs is None or cr_scene_id_mapping is None or obj_data is None:
            logger.error('this params cr_scene_id_mapping or crsceneevent_usersubmitlogs or obj_data is missing')
            raise serializers.ValidationError(error.MISSING_PARAMETERS)

        machine_each_count = obj_data['event_count']['machine_each_count']
        instance['machine_count'] = machine_each_count.get(instance['id'], 0)

        instance['name'] = cr_scene_id_mapping.get(instance['id'], instance['name'])
        mission_ids_list = instance['missions']
        cr_scene_mission_submit_log = crsceneevent_usersubmitlogs.filter(mission_id__in=mission_ids_list)
        cr_scene_mission_submit_log_soved = cr_scene_mission_submit_log.filter(is_solved=True)
        submit_log_mission_ids = set()
        submit_log_is_solved_score = 0

        for cr_scene_mission_submit_log_i in cr_scene_mission_submit_log:
            submit_log_mission_ids.add(cr_scene_mission_submit_log_i.mission_id)
            if cr_scene_mission_submit_log_i.is_solved is True:
                submit_log_is_solved_score += cr_scene_mission_submit_log_i.score
        instance['mission_total_count'] = len(mission_ids_list)
        instance['missioin_participate'] = len(submit_log_mission_ids)
        instance['missioin_submit_count'] = cr_scene_mission_submit_log.count()
        instance['missioin_submit_soved_count'] = cr_scene_mission_submit_log_soved.count()
        instance['submit_log_is_solved_score'] = submit_log_is_solved_score
        return instance
