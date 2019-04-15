# -*- coding: utf-8 -*-
import json
import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions, filters, status, viewsets
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from base.utils import udict
from base.utils.enum import Enum
from base.utils.rest.decorators import request_data
from base.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PMixin, PublicModelMixin
from base_auth.utils.rest.mixins import BatchSetOwnerModelMixin
from base_auth.utils.rest.permissions import IsAdmin
from base_mission import models as mission_models, constant
from base_mission.cms import serializers as cms_mission_serializer
from base_mission.web import serializers as web_mission_serializer
from base_remote.managers import MonitorManager
from base_scene.common.scene import SceneHandler
from base_scene.common.util.constants import StatusUpdateEvent as SceneStatusUpdateEvent
from base_scene.models import Scene, SceneNet, SceneTerminal
from base_scene.web import consumers as scene_consumers
from base_traffic.utils.traffic import get_terminal_info
from cr_scene import models as scene_models
from cr_scene import permission as cr_permissions
from cr_scene.error import error
from cr_scene.utils import common
from cr_scene.utils import uitls as cr_scene_utils
from cr_scene.utils.agent_util import report_sys_info
from cr_scene.utils.mission_util import SceneMissionManager
from cr_scene.utils.scene import get_scene_all_remote_info
from cr_scene.utils.traffic_util import SceneTrafficManager
from cr_scene.utils.vis import VisApi, check_vis_is_run
from cr_scene.web import consumers as cr_scene_consumers
from traffic_event.models import TrafficEvent
from traffic_event.utils.traffic_event_manager import TrafficEventManager
from traffic_event.web.serializers import TrafficEventSerializer
from . import serializers as webserializers

logger = logging.getLogger(__name__)


class CrSceneViewSet(CacheModelMixin,
                     PMixin,
                     viewsets.ReadOnlyModelViewSet):
    queryset = scene_models.CrScene.objects.all()
    serializer_class = webserializers.CrSceneSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)


class CrEventViewSet(BatchSetOwnerModelMixin,
                     DestroyModelMixin,
                     CacheModelMixin,
                     PublicModelMixin,
                     PMixin,
                     viewsets.ModelViewSet):
    queryset = scene_models.CrEvent.objects.all()
    serializer_class = webserializers.CrEventSerializers
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    related_cache_classes = ('cr_scene.cms.api.CrEventViewSet',)
    MISSIONSTATUS = Enum(
        NOTDONE=0,
        FAILE=1,
        SUCCESS=2,
    )
    START_OR_STOP_STATUS = Enum(
        STOP=1,
        START=2
    )
    lookup_value_regex = '[0-9]+'

    def get_cache_key(self):
        """
        缓存力度精确到 每一个用户
        """
        return super(CrEventViewSet, self).get_cache_key() + '--USER%s' % self.request.user.id

    def get_retrieve_cache_key(self):
        view_name = self.__class__.__name__
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        retrieve_key = self.kwargs[lookup_url_kwarg]
        return '{3}--{0}--{1}--retrieve-USER{2}'.format(self.lookup_field, retrieve_key, self.request.user.id,
                                                        view_name)

    def _get_retrieve_data(self):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        return data

    def retrieve(self, request, *args, **kwargs):
        if self.get_cache_flag():
            cache_value = self.cache.get(self.get_retrieve_cache_key())
            if cache_value:
                data = cache_value
            else:
                data = self._get_retrieve_data()
                self.cache.set(self.get_retrieve_cache_key(), data, self.get_cache_age())
        else:
            data = self._get_retrieve_data()
        return Response(data)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return webserializers.CrEventDetailSerializers
        if self.action == 'list':
            return webserializers.CrEventSerializersList
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            queryset = self.get_serializer_class().setup_eager_loading(queryset)

        return queryset

    def get_permissions(self):
        if self.action in ['post', 'patch']:
            return [permission() for permission in (permissions.IsAuthenticated, IsAdmin)]
        elif self.action in ['retrieve']:
            return [permission() for permission in
                    (permissions.IsAuthenticated, cr_permissions.AllPeopleInCrEventPermission)]
        return [permission() for permission in self.permission_classes]

    def sub_perform_create(self, serializer):
        validated_data = serializer.validated_data
        if scene_models.CrEvent.original_objects.filter(name=validated_data['name']).exists():
            raise exceptions.ValidationError(error.NAME_EXISTS)

        with transaction.atomic():
            serializer.save(
                user=self.request.user,
                modify_user=self.request.user,
            )

            cr_scenes = self.shift_data.get('cr_scenes')
            if cr_scenes:
                try:
                    cr_scenes = json.loads(cr_scenes)
                except Exception:
                    pass
                else:
                    update_cr_scenes_data(serializer.instance, cr_scenes)

        return True

    def sub_perform_update(self, serializer):
        validated_data = serializer.validated_data
        if 'name' in validated_data:
            if scene_models.CrEvent.original_objects.exclude(pk=serializer.instance.pk).filter(
                    name=validated_data['name']).exists():
                raise exceptions.ValidationError(error.NAME_EXISTS)

        with transaction.atomic():
            serializer.save(
                modify_time=timezone.now(),
                modify_user=self.request.user,
            )

            cr_scenes = self.shift_data.get('cr_scenes')
            if cr_scenes:
                try:
                    cr_scenes = json.loads(cr_scenes)
                except Exception:
                    pass
                else:
                    update_cr_scenes_data(serializer.instance, cr_scenes)

        return True

    @action(methods=['GET'], detail=True, url_path=r'(?P<cr_scene_id>[0-9]+)/(?P<cr_scene_instance_id>[0-9]+)',
            permission_classes=[permissions.IsAuthenticated, cr_permissions.OnlyOrdinaryWithCrScenePermission])
    def getUserUsedStandardDevice(self, request, pk, cr_scene_id, cr_scene_instance_id):
        self.get_object()
        cr_event_user_standarddevice_serializers = webserializers.CrEventUserStandardDeviceSerializer(
            scene_models.CrEventUserStandardDevice.objects.filter(scene_id=cr_scene_instance_id), many=True) \
            .data
        data = {}
        if cr_event_user_standarddevice_serializers:
            data = cr_scene_utils.list_dict_as_only_one_key_to_new_dict(cr_event_user_standarddevice_serializers,
                                                                        'standard_device')
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path=r'(?P<cr_scene_id>[0-9]+)',
            permission_classes=[permissions.IsAuthenticated, cr_permissions.OnlyOrdinaryWithCrScenePermission])
    def get_ordinary_user_cr_event(self, request, pk, cr_scene_id):
        self.get_object()
        cr_event = request.data.get('_permission_cr_event')
        return Response(data=cr_event, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.AdministratorPermission])
    def update_mission_score(self, request, pk):
        """
        权限管理员
        修改分数 获取得分
        """
        obj = self.get_object()
        score = self.shift_data.get('score', int)
        mission_id = self.shift_data.get('mission_id', int)
        if score is None or mission_id is None:
            raise exceptions.ValidationError(error.IS_NUMBER)

        cr_scene_event_answer = scene_models.CrSceneEventUserAnswer.objects.filter(cr_event=obj,
                                                                                   mission_id=mission_id).first()
        if not cr_scene_event_answer:
            raise exceptions.ValidationError(error.UNFINISHED_MISSION_CANNOT_MODIFY_SCORES)

        serializer = webserializers.CrSceneEventUserAnswerSerializer(cr_scene_event_answer,
                                                                     data={"score": score},
                                                                     partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            last_edit_user=self.request.user
        )
        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.AdministratorPermission])
    def publish_mission(self, request, pk):
        """
        权限： 管理员
        发布任务, 隐藏任务， 已经完成的任务 不能隐藏
        """
        self.get_object()
        mission_id = self.shift_data.get('mission_id', int)
        public = request.data.get('public', None)
        _permission_scene_ids = request.data.get('_permission_scene_ids', [])
        if public is None or mission_id is None:
            raise exceptions.ValidationError(error.MISSING_PARAMETERS)
        if public in ('true', 'false'):
            if public == 'true':
                public = True
            if public == 'false':
                public = False

        mission = mission_models.Mission.objects.filter(crscene__id__in=_permission_scene_ids, id=mission_id).first()
        if not mission:
            raise exceptions.ValidationError(error.NOT_FOUND)
        mission.public = public
        mission.save()
        self.clear_cache()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.AdministratorPermission])
    def get_missions_all(self, request, pk):
        """
        权限：只管理员
        获取任务列表, 多个队伍， 默认未发布， 获取用户是否已做过状态
        """
        obj = self.get_object()
        crscene_objs, cr_event_scene_objs_mapping = cr_scene_utils.get_info_from_administrator_permission(request, obj)

        data_list = []
        for cr_scene in crscene_objs:

            mission_data_dict = {}
            # 队伍名字
            team_name = cr_event_scene_objs_mapping[cr_scene.id]['name']
            cr_scene_instance = cr_event_scene_objs_mapping[cr_scene.id]['cr_scene_instance']
            mission_data_dict['team_name'] = team_name
            mission_data_dict['cr_scene_id'] = cr_scene.id
            mission_data_dict['cr_scene_instance'] = cr_scene_instance

            missions = cr_scene.missions.all()
            missions_ids = [mission.id for mission in missions]

            # submit_log_list = scene_models.CrSceneEventUserSubmitLog.objects.filter(
            #     cr_event=obj,
            #     mission_id__in=missions_ids).values(
            #     'mission_id', 'answer', 'is_solved', 'score')

            checker_mission_list = scene_models.CrSceneEventUserAnswer.objects.filter(
                cr_event=obj,
                mission_id__in=missions_ids).values('mission_id', 'answer', 'score')

            mission_datas = cms_mission_serializer.MissionSerializer(missions, many=True).data
            mission_data_mapping = {mission_data['id']: mission_data for mission_data in mission_datas}

            # mission_data_mapping = cr_scene_utils.mapping_add_data(submit_log_list, mission_data_mapping, True)
            mission_data_mapping = cr_scene_utils.mapping_add_data(checker_mission_list,
                                                                   mission_data_mapping, True, True)
            for mission_data in mission_data_mapping.values():
                if mission_data["period"] in mission_data_dict.keys():
                    mission_data_dict[mission_data["period"]].append(mission_data)
                else:
                    mission_data_dict[mission_data["period"]] = [mission_data]
            data_list.append(mission_data_dict)

        return Response(data=data_list, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path=r'get_missions/(?P<cr_scene_id>[^/.]+)',
            permission_classes=[permissions.IsAuthenticated, cr_permissions.OnlyOrdinaryWithCrScenePermission])
    def get_missions(self, request, pk, cr_scene_id):
        """
        获取红队/蓝队
        已经发布的的任务， 用户是否已经做过, 每条任务对应某个职位
        用户最近提交记录
        """
        obj = self.get_object()
        cr_scenes_ids = list(obj.cr_scenes.values_list('id', flat=True))

        if not cr_scenes_ids or cr_scene_id and int(cr_scene_id) not in cr_scenes_ids:
            raise exceptions.ValidationError(error.NOT_FOUND)

        cr_scene = get_object_or_404(scene_models.CrScene, pk=cr_scene_id)
        missions = cr_scene.missions.filter(public=True)
        missions_ids = [mission.id for mission in missions]
        submit_log_list = scene_models.CrSceneEventUserSubmitLog.objects.filter(
            cr_event=obj,
            mission_id__in=missions_ids,
            is_new=True).values('mission_id', 'answer', 'is_solved')
        checker_mission_list = scene_models.CrSceneEventUserAnswer.objects.filter(
            cr_event=obj,
            mission_id__in=missions_ids).values('mission_id')

        mission_data_dict = {}
        mission_datas = web_mission_serializer.MissionSerializer(missions, many=True).data
        mission_data_mapping = {mission_data['id']: mission_data for mission_data in mission_datas}

        mission_data_mapping = cr_scene_utils.mapping_add_data(submit_log_list, mission_data_mapping, True)
        mission_data_mapping = cr_scene_utils.mapping_add_data(checker_mission_list,
                                                               mission_data_mapping, default_solved=True)

        for mission_data in mission_data_mapping.values():
            if mission_data["period"] in mission_data_dict.keys():
                mission_data_dict[mission_data["period"]].append(mission_data)
            else:
                mission_data_dict[mission_data["period"]] = [mission_data]

        return Response(data=mission_data_dict, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.RefereePermission])
    def get_team_score(self, request, pk):
        """
        权限：只管理员
        获取队伍得分排名, 红队和蓝队
        """
        obj = self.get_object()
        crscene_objs, cr_event_scene_objs_mapping = cr_scene_utils.get_info_from_administrator_permission(request, obj)

        data_list = []
        for cr_scene in crscene_objs:
            mission_data_dict = {}
            # 队伍名字
            team_name = cr_event_scene_objs_mapping[cr_scene.id]['name']
            mission_data_dict['team_name'] = team_name

            missions = cr_scene.missions.all()
            missions_ids = [mission.id for mission in missions]

            answer_list = scene_models.CrSceneEventUserAnswer.objects.filter(cr_event=obj,
                                                                             mission_id__in=missions_ids) \
                .values('score')

            mission_data_dict['score'] = sum([float(item['score']) for item in answer_list])
            mission_data_dict['cr_scene_id'] = cr_scene.id
            data_list.append(mission_data_dict)

        data_list = sorted(data_list, key=lambda x: x['score'], reverse=True)

        return Response(data=data_list, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path=r'user_submit_mission/(?P<cr_scene_id>[^/.]+)',
            permission_classes=[permissions.IsAuthenticated, cr_permissions.OnlyOrdinaryWithCrScenePermission])
    def user_submit_mission(self, request, pk, cr_scene_id):
        """
        用户提交misson
        目前只是判断考试, 已经完成的题目不能进行提交, 试卷型任务只能提交一次, ctf型可以提交多次, 提交正确了的都不能再进行提交
        """
        cr_event_id = pk

        user = request.user
        answer = request.data.get('answer', None)
        mission_id = request.data.get('mission_id', None)

        if not answer or not mission_id:
            raise exceptions.ParseError(error.MISSING_PARAMETERS)
        mission = get_object_or_404(mission_models.Mission, pk=mission_id)

        crsceneeventuseranswer_obj = scene_models.CrSceneEventUserSubmitLog.objects.filter(
            cr_event_id=cr_event_id,
            mission_id=mission_id)

        cr_scene_utils.check_mission_has_down(crsceneeventuseranswer_obj, mission)
        is_solved, score = cr_scene_utils.check_mission_answer(answer, mission)
        data = {
            'user': user,
            'cr_event_id': cr_event_id,
            'mission_id': mission_id,
            'answer': isinstance(answer, dict) and json.dumps(answer) or answer,
            'score': score
        }

        if is_solved:
            scene_models.CrSceneEventUserAnswer.objects.create(**data)
            data['is_solved'] = True
        else:
            data['is_solved'] = False
        scene_models.CrSceneEventUserSubmitLog.objects.filter(**{
            'cr_event_id': cr_event_id,
            'mission_id': mission_id}).update(is_new=False)
        scene_models.CrSceneEventUserSubmitLog.objects.create(**data)
        self.clear_cache()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.AdministratorPermission])
    def control_mission_status(self, request, pk):
        obj = self.get_object()

        cr_scene_instance = self.shift_data.get("scene_id", int)
        mission_id = self.shift_data.get('mission_id', int)
        mission_status = self.shift_data.get('mission_start', int)

        if mission_id is None or mission_status is None or cr_scene_instance is None:
            raise exceptions.ValidationError(error.MISS_PARAMETER)

        if mission_status not in mission_models.Mission.MissionStatus.values():
            raise exceptions.ValidationError(error.MISS_PARAMETER)

        # _permission_scene_ids = request.data.get('_permission_scene_ids', [])

        if not scene_models.CrEventScene.objects.filter(cr_scene_instance=cr_scene_instance, cr_event=obj).exists():
            raise exceptions.ValidationError(error.the_scene_id_does_not_belong_to_the_crevent)

        if mission_status == constant.MissionStatus.ISPROCESS:
            SceneMissionManager(cr_scene_instance, True).start_mission_check(mission_id)
        elif mission_status == constant.MissionStatus.STOP:
            SceneMissionManager(cr_scene_instance, True).stop_mission_check(mission_id)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.AdministratorPermission])
    def get_traffic_events(self, request, pk):
        obj = self.get_object()
        crscene_objs, cr_event_scene_objs_mapping = cr_scene_utils.get_info_from_administrator_permission(request, obj)

        result = []
        for crscene_obj in crscene_objs:
            target_data = {}
            runner_data = {}
            cr_scene_traffic_events = crscene_obj.traffic_events.all()
            # _permission_scene_ids = request.data.get('_permission_scene_ids', None)
            _permission_cr_event_scene_data = request.data.get('_permission_cr_event_scene_data', None)
            scene_data = filter(lambda x: x['cr_scene'] == crscene_obj.id, _permission_cr_event_scene_data)
            cr_scene_instance_id = scene_data[0]['cr_scene_instance'] if scene_data else None
            traffic_datas = TrafficEventSerializer(cr_scene_traffic_events, many=True).data

            for t in traffic_datas:
                t['scene_id'] = crscene_obj.id
                if cr_scene_instance_id:
                    target_name, target_ip, _ = get_terminal_info(cr_scene_instance_id, t['target'], t['target_net'])
                    runner_name, runner_ip, _ = get_terminal_info(cr_scene_instance_id, t['runner'], t['target_net'])
                    target_data = {
                        'target_name': target_name,
                        'target_ip': target_ip,
                    }
                    runner_data = {
                        'runner_name': runner_name,
                        'runner_ip': runner_ip,
                    }
                t['target_data'] = target_data
                t['runner_data'] = runner_data
            result.extend(traffic_datas)
        return Response(data=result, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.AdministratorPermission])
    def start_stop_traffic_event(self, request, pk):
        self.get_object()
        traffic_event_id = request.data.get('traffic_event_id', None)
        is_start = request.data.get('is_start', None)
        is_start = True if is_start == TrafficEvent.Status.RUNNING else False
        scene_id = request.data.get('scene_id', None)
        _permission_scene_ids = request.data.get('_permission_scene_ids', None)
        _permission_cr_event_scene_data = request.data.get('_permission_cr_event_scene_data', None)
        scene_data = filter(lambda x: x['cr_scene'] == scene_id, _permission_cr_event_scene_data)
        cr_scene_instance_id = scene_data[0]['cr_scene_instance'] if scene_data else None
        if cr_scene_instance_id is None or int(scene_id) not in _permission_scene_ids:
            raise exceptions.ValidationError(error.SCENE_ID_IS_NOT_ALLOW)

        if traffic_event_id is None:
            raise exceptions.ValidationError(error.MISSING_PARAMETERS)

        traffic_event = TrafficEvent.objects.filter(crscene__id__in=_permission_scene_ids, id=traffic_event_id).first()
        if not traffic_event:
            raise exceptions.ValidationError(error.NOT_FOUND)

        if traffic_event.status == TrafficEvent.Status.RUNNING == is_start:
            raise exceptions.ValidationError(error.IS_RUNNING)

        traffifc_manager = TrafficEventManager(traffic_event, cr_scene_instance_id)
        if is_start:
            _ret = traffifc_manager.start(manual=True)
            if _ret is None:
                raise exceptions.ValidationError(error.CONNECTION_REFUSED)
        else:
            _ret = traffifc_manager.stop()

        if _ret is None or _ret['status'] != 'ok':
            raise exceptions.ValidationError(error.OPERATION_FAILED)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.RefereePermission])
    def event_report(self, request, pk):
        obj = self.get_object()
        obj_data = webserializers.CrEventSerializers(obj,
                                                     context={'request': self.request}).data  # 包含_permission_scene_ids
        cr_scene_id_mapping = {cr_scene["cr_scene"]["id"]: cr_scene["name"] for cr_scene in obj_data['cr_scenes']}
        crsceneevent_usersubmitlogs = scene_models.CrSceneEventUserSubmitLog.objects.filter(cr_event=obj)

        cr_scene_objs = webserializers.CrSceneModelSerializer(
            scene_models.CrScene.objects.filter(id__in=cr_scene_id_mapping.keys()), many=True).data

        activity_report_data = webserializers.ActivityReportSerializer(cr_scene_objs, context={
            'cr_scene_id_mapping': cr_scene_id_mapping,
            'obj_data': obj_data,
            'crsceneevent_usersubmitlogs': crsceneevent_usersubmitlogs}, many=True).data

        data = {
            'obj_data': obj_data,
            'activity_report_data': activity_report_data,
        }
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['GET', 'POST'], detail=True,
            permission_classes=[permissions.IsAuthenticated, cr_permissions.RefereePermission])
    def monitor(self, request, pk):
        obj = self.get_object()

        cr_event_data = webserializers.CrEventDetailSerializers(obj, context={
            'request': request}).data  # 处理 request cr_scene_id

        def _get_base_connection_info(scene_obj):
            cr_scene_instance = scene_obj.get('cr_scene_instance', None)
            if cr_scene_instance is None:
                return {}, {}, {}

            all_server_connection_ids = get_scene_all_remote_info(scene_obj["cr_scene_instance"])
            key_connnction_server_info = cr_scene_utils.get_deep_dict_value_as_key(all_server_connection_ids)

            monitor_manager = MonitorManager()
            monitor_ret = monitor_manager.share_active_sessions_for_monitor(
                connection_ids=key_connnction_server_info.keys())

            return key_connnction_server_info, monitor_ret, all_server_connection_ids

        if request.method == 'GET':
            # 获取正在使用的机器列表
            scene_obj_serve = []
            for scene_obj in cr_event_data['cr_event_scenes']:
                key_connnction_server_info, monitor_ret, all_server_connection_ids = \
                    _get_base_connection_info(scene_obj)

                server_info_dict = {}
                for connection_id, ret in monitor_ret.items():
                    server_info = key_connnction_server_info.get(connection_id)
                    server_info_dict.setdefault(server_info['machine_id'], {}).update(**server_info)

                if scene_obj["cr_scene_instance_data"] is None:
                    continue
                nodes = scene_obj["cr_scene_instance_data"]["vis_structure"]["nodes"]
                for node in nodes:
                    new_server_info = server_info_dict.get(node['id'], None)
                    if new_server_info is None:
                        continue
                    node.update({
                        'user_id': new_server_info['user_id'],
                        'machine_id': new_server_info['machine_id'],
                        'cr_scene': scene_obj['cr_scene']
                    })
                    scene_obj_serve.append(node)

            return Response(data=scene_obj_serve, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            # 或单个机器的监控链接
            machine_id = self.request.data.get('machine_id')
            # scene_id = self.request.data.get('cr_scene_id') 已经处理
            url = None

            for scene_obj in cr_event_data['cr_event_scenes']:

                key_connnction_server_info, monitor_ret, all_server_connection_ids = _get_base_connection_info(
                    scene_obj)

                machine_user_conection_ids_dict = all_server_connection_ids.get(machine_id, None)
                if machine_user_conection_ids_dict is None:
                    continue

                for connection_id, ret in monitor_ret.items():
                    server_info = key_connnction_server_info.get(connection_id)
                    if server_info['machine_id'] == machine_id:
                        url = ret
                        break
            return Response(data={'url': url}, status=status.HTTP_200_OK)

    def extra_handle_list_data(self, data):
        user = self.request.user
        for row in data:
            cr_scenes = row.pop('cr_scenes', None)
            creventscene_crevent = row['creventscene_crevent']
            if not cr_scenes:
                continue

            user_count, user_role, machine_count = self.get_current_cr_event_and_user_info(cr_scenes,
                                                                                           creventscene_crevent, user)
            row['user_count'] = user_count
            row['event_count'] = {
                'machine_count': machine_count
            }
            if user_role is not None:
                row['role'] = user_role

        return data

    @staticmethod
    def get_current_cr_event_and_user_info(cr_scene_list, creventscene_crevent_list, current_user):
        """
        获取前用户的职位
        :return 用户信息和职位机器信息
        """
        user_roles = None
        cr_scene_user_list = []
        flag = False
        machine_count_dict = {}

        creventscene_crevent_dict = {creventscene_crevent['cr_scene_id']: creventscene_crevent for creventscene_crevent
                                     in creventscene_crevent_list}

        for cr_scene in cr_scene_list:
            creventscene_crevent_data_flag = cr_scene['id'] in creventscene_crevent_dict and True or False
            if creventscene_crevent_data_flag is False or 'roles' not in cr_scene:
                logger.info("we don't get roles_data information from cr_scene in this ==> {}".format(cr_scene))
                continue

            vis_config = cr_scene['scene_config']['vis_config']
            if vis_config is None:
                logger.info('in this CrEventSerializers, we not get vis_config ==> {}'.format(vis_config))
            else:
                machine_count_dict[cr_scene['id']] = len(vis_config['nodes'])

            role_users_mapping_list = creventscene_crevent_dict.get(cr_scene['id'])['roles_data']

            for role_users in role_users_mapping_list:
                user_ids = [user['id'] for user in role_users['users']]
                cr_scene_user_list.extend(user_ids)

            if flag:
                continue

            for roles in role_users_mapping_list:
                if not isinstance(roles['users'], list):
                    logger.info('roles_data format is not list, please check this roles ==> {}'.format(roles))
                    continue
                filter_users = filter(lambda x: x['id'] == current_user.id, roles['users'])
                if len(filter_users) > 0 and flag is False:
                    roles['user'] = filter_users[0]
                    roles['cr_scene_id'] = cr_scene['id']
                    user_roles = roles
                    flag = True
        user_count = len(set(cr_scene_user_list))
        machine_count = sum(machine_count_dict.values())
        return user_count, user_roles, machine_count

    @action(methods=['get', 'post', 'delete'], detail=True)
    def scene(self, request, pk=None):
        cr_event = self.get_object()
        cr_event_scene_ids = self.query_data.getlist('cr_event_scene_ids', int)
        cr_event_scenes = scene_models.CrEventScene.objects.filter(cr_event=cr_event)
        if cr_event_scene_ids:
            cr_event_scenes = cr_event_scenes.filter(pk__in=cr_event_scene_ids)

        if request.method == 'GET':
            for cr_event_scene in cr_event_scenes:
                if not common.can_role_get_scene(request.user.id, cr_event_scene):
                    raise exceptions.PermissionDenied(error.NO_PERMISSION)

            cr_event_scene_datas = webserializers.CrEventSceneSeriallizer(
                cr_event_scenes,
                fields=('id', 'cr_scene_instance_data'),
                context={'user': request.user},
                many=True,
            ).data

            data = {cr_event_scene_data['id']: cr_event_scene_data['cr_scene_instance_data'] for cr_event_scene_data in
                    cr_event_scene_datas}

            return Response(data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            for cr_event_scene in cr_event_scenes:
                if not common.can_role_control_scene(request.user.id, cr_event_scene):
                    raise exceptions.PermissionDenied(error.NO_PERMISSION)

            for cr_event_scene in cr_event_scenes:
                if cr_event_scene.cr_scene_instance:
                    delete_cr_event_scene_instance(request.user, cr_event_scene)

                handler = SceneHandler(request.user)
                scene_instance = handler.create(cr_event_scene.cr_scene.scene_config, status_updated={
                    'func': _cr_event_scene_instance_status_updated,
                    'params': {
                        'user_id': request.user.pk,
                        'cr_event_scene_id': cr_event_scene.pk,
                    }
                })
                cr_event_scene.cr_scene_instance = scene_instance
                try:
                    cr_event_scene.save()
                except Exception:
                    delete_cr_event_scene_instance(request.user, cr_event_scene)

            self.clear_cache()
            users = common.get_users_by_cr_event_scenes(cr_event_scenes)
            for user in users:
                cr_scene_consumers.CrEventSceneWebsocket.cr_event_start(user, cr_event)

            cr_event_scene_datas = webserializers.CrEventSceneSeriallizer(
                cr_event_scenes,
                fields=('id', 'cr_scene_instance_data'),
                context={'user': request.user},
                many=True,
            ).data
            data = {cr_event_scene_data['id']: cr_event_scene_data['cr_scene_instance_data'] for cr_event_scene_data in
                    cr_event_scene_datas}

            return Response(data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            for cr_event_scene in cr_event_scenes:
                if not common.can_role_control_scene(request.user.id, cr_event_scene):
                    raise exceptions.PermissionDenied(error.NO_PERMISSION)

            for cr_event_scene in cr_event_scenes:
                if cr_event_scene.cr_scene_instance:
                    delete_cr_event_scene_instance(request.user, cr_event_scene)

            self.clear_cache()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def scene_terminal_restart(self, request, pk=None):
        cr_event = self.get_object()
        try:
            scene_terminal_id = self.shift_data.get('id', int)
            scene_terminal = SceneTerminal.objects.get(pk=scene_terminal_id)
        except Exception:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        cr_event_scenes = scene_models.CrEventScene.objects.filter(cr_event=cr_event)
        scene_id_cr_event_scene = {
            cr_event_scene.cr_scene_instance_id: cr_event_scene
            for cr_event_scene in cr_event_scenes
            if cr_event_scene.cr_scene_instance_id
        }
        cr_event_scene = scene_id_cr_event_scene.get(scene_terminal.scene_id)

        if not cr_event_scene or not common.can_role_control_terminal(request.user.id, cr_event_scene,
                                                                      scene_terminal.sub_id):
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

        handler = SceneHandler(request.user, scene=cr_event_scene.cr_scene_instance)
        handler.restart_terminal(scene_terminal=scene_terminal)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def scene_terminal_recreate(self, request, pk=None):
        cr_event = self.get_object()
        try:
            scene_terminal_id = self.shift_data.get('id', int)
            scene_terminal = SceneTerminal.objects.get(pk=scene_terminal_id)
        except Exception:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        cr_event_scenes = scene_models.CrEventScene.objects.filter(cr_event=cr_event)
        scene_id_cr_event_scene = {
            cr_event_scene.cr_scene_instance_id: cr_event_scene
            for cr_event_scene in cr_event_scenes
            if cr_event_scene.cr_scene_instance_id
        }
        cr_event_scene = scene_id_cr_event_scene.get(scene_terminal.scene_id)

        if not cr_event_scene or not common.can_role_control_scene(request.user.id, cr_event_scene):
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

        handler = SceneHandler(request.user, scene=cr_event_scene.cr_scene_instance)
        handler.recreate_terminal(scene_terminal=scene_terminal)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def console_url(self, request, pk=None):
        cr_event = self.get_object()

        try:
            scene_terminal_id = self.query_data.get('id', int)
            scene_terminal = SceneTerminal.objects.get(pk=scene_terminal_id)
        except Exception:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        cr_event_scenes = scene_models.CrEventScene.objects.filter(cr_event=cr_event)
        scene_id_cr_event_scene = {
            cr_event_scene.cr_scene_instance_id: cr_event_scene
            for cr_event_scene in cr_event_scenes
            if cr_event_scene.cr_scene_instance_id
        }
        cr_event_scene = scene_id_cr_event_scene.get(scene_terminal.scene_id)

        if not cr_event_scene or not common.can_role_get_terminal(request.user.id, cr_event_scene,
                                                                  scene_terminal.sub_id):
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

        handler = SceneHandler(request.user)
        url = handler.get_console_url(scene_terminal)
        return Response({'url': url})


def update_cr_scenes_data(cr_event, cr_scenes):
    old_cr_scenes = scene_models.CrEventScene.objects.filter(cr_event=cr_event)
    id_old_cr_scene = {cr_scene.id: cr_scene for cr_scene in old_cr_scenes}

    fields = ('cr_scene', 'name', 'roles', 'extra')
    for cr_scene in cr_scenes:
        cr_scene_id = cr_scene.get('id')
        if cr_scene_id:
            old_cr_scene = id_old_cr_scene.pop(cr_scene_id)
            update_params = udict.diff(webserializers.CrEventSceneSeriallizer(old_cr_scene, fields=fields).data,
                                       cr_scene, fields)
            if update_params:
                if 'cr_scene' in update_params:
                    update_params['cr_scene_id'] = update_params.pop('cr_scene')
                scene_models.CrEventScene.objects.filter(pk=old_cr_scene.pk).update(**update_params)
        else:
            create_params = udict.diff({}, cr_scene, fields)
            if 'cr_scene' in create_params:
                create_params['cr_scene_id'] = create_params.pop('cr_scene')
            scene_models.CrEventScene.objects.create(
                cr_event=cr_event,
                **create_params
            )

    for cr_scene in id_old_cr_scene.values():
        cr_scene.delete()


def _cr_event_scene_instance_status_updated(user_id, cr_event_scene_id, *args, **kwargs):
    CrEventViewSet.clear_self_cache()
    try:
        cr_event_scene = scene_models.CrEventScene.objects.filter(pk=cr_event_scene_id).values(
            'cr_event_id',
            'roles',
            'cr_scene__roles',
            'cr_scene__scene_config__json_config',
            'cr_scene_instance__json_config',
        )[0]
        role_users_list = json.loads(cr_event_scene['roles'])
        scene_json_config = json.loads(
            cr_event_scene['cr_scene_instance__json_config'] or cr_event_scene['cr_scene__scene_config__json_config'])

        # 由于业务场景合并，需要向其它场景人员推送
        other_cr_event_scenes = scene_models.CrEventScene.objects.exclude(pk=cr_event_scene_id).filter(
            cr_event=cr_event_scene['cr_event_id']).values('roles')
        other_role_users_list_collection = []
        for other_cr_event_scene in other_cr_event_scenes:
            other_role_users_list = json.loads(other_cr_event_scene['roles'])
            other_role_users_list_collection.append(other_role_users_list)
    except Exception as e:
        logger.error('get event role users config error: %s', e)
        return

    user_ids = {user_id}
    for role_users in role_users_list:
        user_ids.update(role_users.get('users', []))

    other_user_ids = set()
    for other_role_users_list in other_role_users_list_collection:
        for other_role_users in other_role_users_list:
            other_user_ids.update(other_role_users.get('users', []))
    other_user_ids = other_user_ids - user_ids
    public_data_ids = common.get_public_data_ids(scene_json_config) if other_user_ids else []

    event = kwargs.get('event', SceneStatusUpdateEvent.SCENE_CREATE)
    status = kwargs.get('status')
    scene_id = kwargs.get('scene_id')
    if scene_id:
        scene = kwargs.get('scene')

        if status == Scene.Status.RUNNING:
            if event == SceneStatusUpdateEvent.SCENE_CREATE:
                # 场景创建完成
                logger.info('cr scene created')

                # 流量发生开始
                SceneTrafficManager(scene_id).start_traffic_event()

                # 检测任务开始
                SceneMissionManager(scene_id, True).start_mission_check()
        elif status == Scene.Status.DELETED:
            # 删除流量
            SceneTrafficManager(scene_id).stop_traffic_event()

            # 删除检测任务
            SceneMissionManager(scene_id, True).stop_mission_check()
        else:
            pass

        for user_id in user_ids:
            scene_consumers.SceneWebsocket.scene_status_update(user_id, scene or scene_id)

        for user_id in other_user_ids:
            scene_consumers.SceneWebsocket.scene_status_update(user_id, scene or scene_id)

    scene_net_id = kwargs.get('scene_net_id')
    if scene_net_id:
        scene_net = kwargs.get('scene_net')

        for user_id in user_ids:
            scene_consumers.SceneWebsocket.scene_net_status_update(user_id, scene_net or scene_net_id)

        if other_user_ids and public_data_ids:
            if scene_net:
                scene_net_sub_id = scene_net.sub_id
            else:
                try:
                    scene_net_sub_id = SceneNet.objects.filter(pk=scene_net_id).values('sub_id')[0]['sub_id']
                except Exception:
                    scene_net_sub_id = None
            if scene_net_sub_id and scene_net_sub_id in public_data_ids:
                for user_id in other_user_ids:
                    scene_consumers.SceneWebsocket.scene_net_status_update(user_id, scene_net or scene_net_id)

    scene_terminal_id = kwargs.get('scene_terminal_id')
    if scene_terminal_id:
        scene_terminal = kwargs.get('scene_terminal')

        if status == SceneTerminal.Status.RUNNING:
            if event == SceneStatusUpdateEvent.SCENE_CREATE:
                # 机器创建完成
                # report_sys_info(cr_event_scene_id, scene_terminal_id)
                from base.utils.thread import async_exe
                async_exe(report_sys_info, (cr_event_scene['cr_event_id'], scene_terminal_id), delay=10)

        if scene_terminal:
            scene_terminal_sub_id = scene_terminal.sub_id
        else:
            try:
                scene_terminal_sub_id = SceneTerminal.objects.filter(pk=scene_terminal_id).values('sub_id')[0]['sub_id']
            except Exception as e:
                logger.error('get scene_terminal error: %s', e)
                return
        try:
            role_servers_list = json.loads(cr_event_scene['cr_scene__roles'])
            role_users_mapping = {role_users['role']: role_users['users'] for role_users in role_users_list}
        except Exception as e:
            logger.error('get event role servers config error: %s', e)
            return

        access_users = set()
        for role_servers in role_servers_list:
            role = role_servers.get('value')
            servers = role_servers.get('servers')
            users = role_users_mapping.get(role)
            if role and servers and users and scene_terminal_sub_id in servers:
                access_users.update(users)

        forbid_users = user_ids - access_users
        for user_id in access_users:
            scene_consumers.SceneWebsocket.scene_terminal_status_update(user_id, scene_terminal or scene_terminal_id)
        for user_id in forbid_users:
            scene_consumers.SceneWebsocket.scene_terminal_status_update(user_id, scene_terminal or scene_terminal_id,
                                                                        fields=common.role_terminal_fields.FORBID)

        if other_user_ids and public_data_ids and scene_terminal_sub_id in public_data_ids:
            for user_id in other_user_ids:
                scene_consumers.SceneWebsocket.scene_terminal_status_update(
                    user_id,
                    scene_terminal or scene_terminal_id,
                    fields=common.role_terminal_fields.PUBLIC,
                    data_handler=common.handle_public_terminal_data,
                )


def delete_cr_event_scene_instance(user, cr_event_scene, raise_exception=False):
    handler = SceneHandler(user, scene=cr_event_scene.cr_scene_instance)
    handler.delete()

    cr_event_scene.cr_scene_instance = None
    try:
        cr_event_scene.save()
    except Exception as e:
        logger.error('cr event scene save error: %s', e)
        if raise_exception:
            raise exceptions.APIException(error.SAVE_FAILED)
        else:
            return False
    else:
        return True


class EventNoticeViewSet(BatchSetOwnerModelMixin,
                         DestroyModelMixin,
                         CacheModelMixin,
                         PublicModelMixin,
                         PMixin,
                         viewsets.ModelViewSet):
    queryset = scene_models.EventNotice.objects.all()
    serializer_class = webserializers.EventNoticeSerializer
    permission_classes = (permissions.IsAuthenticated, cr_permissions.CrEventAllowAnyNoObjPermission)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    unlimit_pagination = True
    permission_query_param = 'cr_event'

    def get_permissions(self):
        if self.action in ('create', 'destory',):
            return [permissions.IsAuthenticated(), cr_permissions.AdministratorNoObjectPermission()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        queryset = self.queryset

        cr_event_id = self.query_data.get(self.permission_query_param, int)
        if cr_event_id:
            queryset = queryset.filter(cr_event_id=cr_event_id)

        return queryset

    def sub_perform_create(self, serializer):
        serializer.save(
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True


class AgentViewSet(CacheModelMixin,
                   PublicModelMixin,
                   PMixin,
                   viewsets.ModelViewSet):
    queryset = scene_models.MissionAgentUpload.objects.all()
    serializer_class = webserializers.AgentSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset

        cr_event_id = self.query_data.get('cr_event_id', int)
        if cr_event_id:
            queryset = queryset.filter(cr_event_id=cr_event_id)

        machine_id = self.query_data.get('machine_id')
        if machine_id:
            queryset = queryset.filter(machine_id=machine_id)

        return queryset

    def sub_perform_create(self, serializer):
        logger.debug(self.request.META)
        logger.debug(self.request.POST)
        serializer.save()
        return True

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)


class CrEventUserStandardDeviceViewSet(CacheModelMixin,
                                       PublicModelMixin,
                                       PMixin,
                                       viewsets.ModelViewSet):
    queryset = scene_models.CrEventUserStandardDevice.objects.all()
    serializer_class = webserializers.CrEventUserStandardDeviceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset

        scene_id = self.query_data.get('scene_id', int)
        if scene_id:
            queryset = queryset.filter(scene_id=scene_id)

        return queryset

    def perform_check(self, serializer):
        # 一个scene_id下的机器是唯一的
        standard_device = serializer.validated_data.get('standard_device')
        scene_id = serializer.validated_data.get('scene_id')
        queryset = self.queryset.filter(scene_id=scene_id, standard_device=standard_device)
        return queryset and True or False

    def sub_perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            modify_user=self.request.user,
        )
        return True


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def show_vis(request, pk):
    if not check_vis_is_run():
        raise exceptions.ValidationError(error.SITUATION_SERVICE_NOT_START_CALL_ADMIN)
    try:
        vis_api = VisApi(pk)
        vis_api.loading(request)
        vis_api.exe_sync_attack(request)
    except Exception as e:
        logger.error('VisApi create error is: %s', e)
        raise exceptions.ValidationError(error.VIS_START_FAILED)
    return Response(status=status.HTTP_200_OK)
