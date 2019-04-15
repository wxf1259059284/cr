# -*- coding: utf-8 -*-
import json
import logging
import re

from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base.utils import udict
from base.utils.enum import Enum
from base.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PMixin
from base_auth.utils.rest.mixins import BatchSetOwnerModelMixin
from base_mission.cms.serializers import MissionSerializer
from base_mission.utils.mission_data_handle import save_related_mission
from base_scene.cms import consumers as scene_consumers
from base_scene.cms.serializers import SceneConfigSerializer
from base_scene.common.scene import SceneHandler
from base_scene.common.util.constants import StatusUpdateEvent as SceneStatusUpdateEvent
from base_scene.models import Scene, SceneTerminal
from base_traffic.utils.traffic import copy_traffic
from cr_scene.models import CrScene, CrEvent, CrEventScene, MissionPeriod
from cr_scene.utils.agent_util import report_sys_info
from cr_scene.utils.mission_util import SceneMissionManager
from cr_scene.utils.traffic_util import SceneTrafficManager
from traffic_event.cms.serializers import TrafficEventSerializer
from traffic_event.utils.event_data_handle import save_related_traffic
from . import serializers as mserializers
from .error import error

logger = logging.getLogger(__name__)


class CrSceneViewSet(BatchSetOwnerModelMixin,
                     DestroyModelMixin,
                     CacheModelMixin,
                     PMixin,
                     viewsets.ModelViewSet):
    queryset = CrScene.objects.all()
    serializer_class = mserializers.CrSceneSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    check_type = Enum(
        MISSIONS='missions',
        TRAFFICEVENTS='traffic_events',
    )
    related_cache_classes = ('cr_scene.web.api.CrSceneViewSet',)

    def sub_perform_create(self, serializer):
        vis_config = self.request.data.get('vis_config')
        vis_file = self.request.data.get('vis_file')
        with transaction.atomic():
            scene_serializer = SceneConfigSerializer(data={'vis_config': vis_config, 'scene_file': vis_file},
                                                     context={'user': self.request.user})
            scene_serializer.is_valid(raise_exception=True)
            scene_instance = scene_serializer.save(user=self.request.user,
                                                   modify_user=self.request.user)
            serializer.save(
                scene_config=scene_instance
            )
        return True

    @action(methods=['post'], detail=False)
    def create_missions(self, request):
        data = request.data
        cr_scene_id = data.get('cr_scene_id', None)

        if not cr_scene_id:
            raise exceptions.NotFound('cr scene not found')

        try:
            cr_scene_instance = CrScene.objects.get(id=cr_scene_id)
            scene_machines = SceneConfigSerializer(cr_scene_instance.scene_config).data.get('vis_config').get('nodes')
            scene_targets = [machine.get('id') for machine in scene_machines if
                             (machine.get('data').get('_category') != 'network')]
            scene_nets = [machine.get('id') for machine in scene_machines if
                          (machine.get('data').get('_category') == 'network')]
        except Exception:
            raise exceptions.ValidationError('Invalid cr_scene_id')

        if data.get('target'):
            if not data.get('target') in scene_targets:
                raise exceptions.ValidationError('Invalid target')

        if data.get('target_net'):
            if not data.get('target_net') in scene_nets:
                raise exceptions.ValidationError('Invalid target_net')

        with transaction.atomic():
            mission_serializer = MissionSerializer(data=data, context={'request': request})
            mission_serializer.is_valid(raise_exception=True)
            mission = mission_serializer.save(
                create_user=self.request.user,
                last_edit_user=self.request.user,
            )
            save_related_mission(mission, data)
            cr_scene_instance.missions.add(mission)

            request.data.update({'id': mission.id})

        headers = self.get_success_headers(request.data)
        return Response(request.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['post'], detail=False)
    def create_traffic_events(self, request):
        # 事件 , 类型
        traffic_id = request.data.get('traffic')
        traffic = copy_traffic(traffic_id)
        cr_scene_id = request.data.get('cr_scene_id', None)
        if not cr_scene_id:
            raise exceptions.NotFound('cr scene not found')

        with transaction.atomic():
            traffic_serializer = TrafficEventSerializer(data=request.data, context={'request': request})
            traffic_serializer.is_valid(raise_exception=True)
            traffic_instance = traffic_serializer.save(
                traffic=traffic,
                create_user=request.user,
                last_edit_user=request.user,
            )
            save_related_traffic(request, traffic)
            cr_scene_instance = get_object_or_404(CrScene, id=cr_scene_id)
            cr_scene_instance.traffic_events.add(traffic_instance)

        headers = self.get_success_headers(request.data)
        return Response(request.data, status=status.HTTP_201_CREATED, headers=headers)

    def sub_perform_update(self, serializer):
        instance = serializer.instance
        vis_config = self.request.data.get('vis_config')
        vis_file = self.request.data.get('vis_file')
        validated_data = serializer.validated_data
        name = validated_data.get('name')
        if not name:
            raise exceptions.ParseError('name is required')
        with transaction.atomic():
            scene_serializer = SceneConfigSerializer(instance.scene_config,
                                                     data={'vis_config': vis_config, 'scene_file': vis_file},
                                                     context={'user': self.request.user}, partial=True)
            scene_serializer.is_valid(raise_exception=True)
            scene_serializer.save(modify_user=self.request.user)
            serializer.save()

        return True

    @action(methods=['delete'], detail=False)
    def batch_destroy_mission_or_traffic_event(self, request):
        # 删除一个或者多个mission, traffice
        ids = self.shift_data.getlist('ids', int)
        cr_scene_id = request.data.get('cr_scene_id', None)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        deleteType = request.data.get('deleteType', None)
        if deleteType not in self.check_type.values():
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not cr_scene_id:
            return Response(status=status.HTTP_204_NO_CONTENT)

        instance = get_object_or_404(CrScene, pk=cr_scene_id)
        manytomany_queryset = getattr(instance, deleteType)
        queryset = manytomany_queryset.filter(id__in=ids)
        if self.perform_batch_destroy(queryset):
            getattr(instance, deleteType).remove(*queryset)

        if hasattr(self, 'clear_cache'):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def prepare_scene(self, request, pk=None):
        cr_scene = self.get_object()
        if cr_scene.scene:
            delete_cr_scene_instance(request.user, cr_scene)

        handler = SceneHandler(request.user)
        scene = handler.create(cr_scene.scene_config, status_updated={
            'func': _cr_scene_instance_status_updated,
            'params': {
                'user_id': request.user.pk,
                'cr_scene_id': cr_scene.pk,
            }
        }, prepare=True, super_viewer=True)
        cr_scene.scene = scene
        try:
            cr_scene.save()
        except Exception:
            delete_cr_scene_instance(request.user, cr_scene)
            raise exceptions.APIException(error.SAVE_FAILED)

        self.clear_cache()

        data = mserializers.CrSceneSerializer(cr_scene, fields=('scene_data',), context={'user': request.user}).data

        return Response(data['scene_data'], status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post', 'delete'], detail=True)
    def scene(self, request, pk=None):
        cr_scene = self.get_object()

        if request.method == 'GET':
            data = mserializers.CrSceneSerializer(cr_scene, fields=('scene_data',), context={'user': request.user}).data
            return Response(data['scene_data'], status=status.HTTP_200_OK)
        elif request.method == 'POST':
            if cr_scene.scene:
                delete_cr_scene_instance(request.user, cr_scene)

            handler = SceneHandler(request.user)
            scene = handler.create(cr_scene.scene_config, status_updated={
                'func': _cr_scene_instance_status_updated,
                'params': {
                    'user_id': request.user.pk,
                    'cr_scene_id': cr_scene.pk,
                }
            }, super_viewer=True)
            cr_scene.scene = scene
            try:
                cr_scene.save()
            except Exception:
                delete_cr_scene_instance(request.user, cr_scene)
                raise exceptions.APIException(error.SAVE_FAILED)

            self.clear_cache()

            data = mserializers.CrSceneSerializer(cr_scene, fields=('scene_data',), context={'user': request.user}).data

            return Response(data['scene_data'], status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if cr_scene.scene:
                delete_cr_scene_instance(request.user, cr_scene)

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def scene_terminal_restart(self, request, pk=None):
        cr_scene = self.get_object()
        terminal_id = self.shift_data.get('id', int)
        if not terminal_id or not cr_scene.scene or not cr_scene.scene.sceneterminal_set.filter(
                pk=terminal_id).exists():
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

        handler = SceneHandler(request.user, scene=cr_scene.scene)
        handler.restart_terminal(scene_terminal=terminal_id)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def scene_terminal_recreate(self, request, pk=None):
        cr_scene = self.get_object()
        terminal_id = self.shift_data.get('id', int)
        if not terminal_id or not cr_scene.scene or not cr_scene.scene.sceneterminal_set.filter(
                pk=terminal_id).exists():
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

        handler = SceneHandler(request.user, scene=cr_scene.scene)
        handler.recreate_terminal(scene_terminal=terminal_id)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def scene_terminal_create_prepared(self, request, pk=None):
        cr_scene = self.get_object()
        terminal_id = self.shift_data.get('id', int)
        if not terminal_id or not cr_scene.scene or not cr_scene.scene.sceneterminal_set.filter(
                pk=terminal_id).exists():
            raise exceptions.PermissionDenied(error.NO_PERMISSION)

        handler = SceneHandler(request.user, scene=cr_scene.scene)
        handler.create_prepared_terminal(scene_terminal=terminal_id)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def console_url(self, request, pk=None):
        cr_scene = self.get_object()

        if not cr_scene.scene:
            raise exceptions.PermissionDenied()

        try:
            scene_terminal_id = self.query_data.get('id', int)
            scene_terminal = cr_scene.scene.sceneterminal_set.filter(pk=scene_terminal_id).first()
            if not scene_terminal:
                raise Exception()
        except Exception:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        handler = SceneHandler(request.user)
        url = handler.get_console_url(scene_terminal)
        return Response({'url': url})


def _cr_scene_instance_status_updated(user_id, cr_scene_id, *args, **kwargs):
    CrSceneViewSet.clear_self_cache()
    event = kwargs.get('event', SceneStatusUpdateEvent.SCENE_CREATE)
    status = kwargs.get('status')
    scene_id = kwargs.get('scene_id')
    if scene_id:
        if status == Scene.Status.RUNNING:
            if event == SceneStatusUpdateEvent.SCENE_CREATE:
                # 场景创建完成
                logger.info('cr scene created')

                # 流量发生开始
                SceneTrafficManager(scene_id, False).start_traffic_event()

                # 检测任务开始
                SceneMissionManager(scene_id, False).start_mission_check()

        elif status == Scene.Status.DELETED:
            # 删除流量
            SceneTrafficManager(scene_id, False).stop_traffic_event()

            # 删除检测任务
            SceneMissionManager(scene_id, False).stop_mission_check()

        scene_consumers.SceneWebsocket.scene_status_update(user_id, scene_id)

    scene_net_id = kwargs.get('scene_net_id')
    if scene_net_id:
        scene_consumers.SceneWebsocket.scene_net_status_update(user_id, scene_net_id)

    scene_terminal_id = kwargs.get('scene_terminal_id')
    if scene_terminal_id:
        if status == SceneTerminal.Status.RUNNING:
            if event == SceneStatusUpdateEvent.SCENE_CREATE:
                # 机器创建完成
                # report_sys_info(cr_scene_id, scene_terminal_id)
                from base.utils.thread import async_exe
                async_exe(report_sys_info, (cr_scene_id, scene_terminal_id), delay=1)

        scene_consumers.SceneWebsocket.scene_terminal_status_update(user_id, scene_terminal_id)


class CrEventViewSet(BatchSetOwnerModelMixin, DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = CrEvent.objects.all()
    serializer_class = mserializers.CrEventSeriallizer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    related_cache_classes = ('cr_scene.cms.web.CrEventViewSet',)

    def get_queryset(self):
        queryset = self.queryset
        return queryset

    def sub_perform_create(self, serializer):
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


def update_cr_scenes_data(cr_event, cr_scenes):
    old_cr_scenes = CrEventScene.objects.filter(cr_event=cr_event)
    id_old_cr_scene = {cr_scene.id: cr_scene for cr_scene in old_cr_scenes}

    fields = ('cr_scene', 'name', 'roles', 'extra')
    for cr_scene in cr_scenes:
        cr_scene_id = cr_scene.get('id')
        if cr_scene_id:
            old_cr_scene = id_old_cr_scene.pop(cr_scene_id)
            update_params = udict.diff(mserializers.CrEventSceneSeriallizer(old_cr_scene, fields=fields).data, cr_scene,
                                       fields)
            if update_params:
                if 'cr_scene' in update_params:
                    update_params['cr_scene_id'] = update_params.pop('cr_scene')
                CrEventScene.objects.filter(pk=old_cr_scene.pk).update(**update_params)
        else:
            create_params = udict.diff({}, cr_scene, fields)
            if 'cr_scene' in create_params:
                create_params['cr_scene_id'] = create_params.pop('cr_scene')
            CrEventScene.objects.create(
                cr_event=cr_event,
                **create_params
            )

    for cr_scene in id_old_cr_scene.values():
        cr_scene.delete()


def delete_cr_scene_instance(user, cr_scene):
    handler = SceneHandler(user, scene=cr_scene.scene)
    handler.delete()

    cr_scene.scene = None
    try:
        cr_scene.save()
    except Exception as e:
        logger.error('cr scene save error: %s', e)
        raise exceptions.APIException(error.SAVE_FAILED)


class MissionPeriodViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = MissionPeriod.objects.all()
    serializer_class = mserializers.MissionPeriodSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('period_name',)

    def get_queryset(self):
        queryset = self.queryset
        data = self.request.query_params

        cr_scene_id = data.get('cr_scene_id')
        if cr_scene_id is not None:
            if re.compile(r'\d*$').match(str(cr_scene_id)):
                queryset = queryset.filter(cr_scene_id=cr_scene_id)
            else:
                raise exceptions.ValidationError('Invalid cr_scene_id')

        return queryset

    @action(methods=['POST'], detail=False)
    def bulk_create_update(self, request):
        data = request.data
        cr_scene_id = data.get('cr_scene_id')
        if cr_scene_id is not None:
            try:
                cr_scene = CrScene.objects.get(id=cr_scene_id)
            except Exception:
                raise exceptions.ValidationError('Invalid cr_scene_id')
        else:
            raise exceptions.ValidationError('cr_scene_id Required')
        periods = data.get('periods')

        if periods is None:
            raise exceptions.ValidationError('periods Required')

        if type(periods) != list:
            raise exceptions.ValidationError('Periods Should Be a List')

        if len(set(periods)) != len(periods):
            raise exceptions.ValidationError('Duplicate Period Name')

        exist_periods = MissionPeriod.objects.filter(cr_scene_id=cr_scene_id).order_by('period_index')
        exist_periods_list = [period.get('period_name') for period in exist_periods.values('period_name')]

        len_new = len(periods)
        len_old = len(exist_periods_list)

        if len_new == len_old:
            for index, period in enumerate(periods):
                update_data = {'period_name': period}
                createUpdateMissionPeriod(data=update_data, cr_scene=cr_scene, isUpdate=True,
                                          existId=exist_periods[index].id)
            self.clear_cache()
            return Response(status=status.HTTP_200_OK)

        elif len_new > len_old:
            for index, period in enumerate(exist_periods_list):
                update_data = {'period_name': periods[index]}
                createUpdateMissionPeriod(data=update_data, cr_scene=cr_scene, isUpdate=True,
                                          existId=exist_periods[index].id)

            for num in range(len_old, len_new):
                period = {
                    'cr_scene': cr_scene_id,
                    'period_name': periods[num],
                    'period_index': num,
                }
                createUpdateMissionPeriod(data=period, cr_scene=cr_scene)
            self.clear_cache()
            return Response(status=status.HTTP_200_OK)

        else:
            for index, period in enumerate(periods):
                update_data = {
                    'period_name': periods[index],
                    'period_index': index,
                }
                createUpdateMissionPeriod(data=update_data, cr_scene=cr_scene, isUpdate=True,
                                          existId=exist_periods[index].id)

            update_list = []
            for num in range(len_new, len_old):
                update_list.append(exist_periods[num].id)

            MissionPeriod.objects.filter(id__in=update_list).update(status=MissionPeriod.Status.DELETE)

            self.clear_cache()
            return Response(status=status.HTTP_200_OK)


def createUpdateMissionPeriod(data, cr_scene, isUpdate=False, existId=None):
    if isUpdate:
        mission_period = MissionPeriod.objects.filter(id=existId).first()
        serializer = mserializers.MissionPeriodSerializer(mission_period, data=data, partial=True)
    else:
        serializer = mserializers.MissionPeriodSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save(cr_scene=cr_scene)
