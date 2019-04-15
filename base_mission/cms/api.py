# -*- coding: utf-8 -*-
from django.db import transaction
import os
from rest_framework.response import Response

from base_mission import models as mission_models, constant
from base_mission.error import error
from base_mission.utils.check_ctf_handler import get_remote_script_device
from base_mission.utils.mission_data_handle import save_related_mission
from base_mission.utils.handle_func import check_required_valid

from cr import settings
from cr_scene.utils.mission_util import SceneMissionManager
from . import serializers as mission_serializer
from base.utils.rest.mixins import CacheModelMixin, PMixin, DestroyModelMixin
from cr_scene.models import CrScene

from rest_framework import viewsets, filters, status, permissions, exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from base.utils.rest.decorators import request_data


class MissionViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = mission_models.Mission.objects.all()
    serializer_class = mission_serializer.MissionSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset

        mission_type = self.query_data.get('type', int)
        if mission_type is not None:
            queryset = queryset.filter(type=mission_type)

        cr_scene_id = self.query_data.get('cr_scene_id')
        if cr_scene_id is not None:
            queryset = CrScene.objects.get(id=cr_scene_id).missions.all()

        return queryset

    def sub_perform_create(self, serializer):
        with transaction.atomic():
            super(MissionViewSet, self).sub_perform_create(serializer)
            mission = serializer.instance
            data = self.request.data

            save_related_mission(mission, data)

        serializer.save(
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        with transaction.atomic():
            super(MissionViewSet, self).sub_perform_update(serializer)
            mission = serializer.instance
            data = self.request.data

            save_related_mission(mission, data, update=True)

            serializer.save(
                last_edit_user=self.request.user,
            )

            return True

    @action(methods=['POST'], detail=False)
    def need_remove_checker(self, request):
        """
        返回需要在拓扑中移除的checker机器
        """
        data = request.query_params
        cr_scene_id = data.get('cr_scene_id')
        check_missions = CrScene.objects.get(id=cr_scene_id).missions.filter(type=constant.Type.CHECK,
                                                                             status=constant.Status.NORMAL)
        checkers = [mission.checkmission.checker_id for mission in check_missions if
                    (mission.checkmission.check_type == constant.CheckType.SYSTEM)]
        checker_ids = data.getlist('checker_id')
        remove_checker = [checker for checker in set(checker_ids) if
                          (checker_ids.count(checker) == checkers.count(checker))]
        return Response(status=status.HTTP_200_OK, data=remove_checker)

    @action(methods=['POST'], detail=False)
    def should_add_checker(self, request):
        """
        判断是否需要在场景中添加checker机器
        """
        data = request.query_params
        cr_scene_id = data.get('cr_scene_id')
        target_net = data.get('target_net')
        script = data.get('script')
        removed_checker = data.get('removed_checker')

        required_fields = ['cr_scene_id', 'target_net', 'script']
        check_required_valid(data, required_fields)

        target_attr = (get_remote_script_device(script), target_net)
        check_missions = CrScene.objects.get(id=cr_scene_id).missions.filter(type=constant.Type.CHECK,
                                                                             status=constant.Status.NORMAL)
        system_check_missions = [mission.checkmission for mission in check_missions if
                                 (mission.checkmission.check_type == constant.CheckType.SYSTEM)]

        if removed_checker:
            removed_missions = [check_mission for check_mission in system_check_missions if
                                (check_mission.checker_id == removed_checker)]
            for removed_mission in removed_missions:
                system_check_missions.remove(removed_mission)

        for mission in system_check_missions:
            if target_attr == (get_remote_script_device(mission.scripts), mission.target_net):
                return Response(status=status.HTTP_200_OK, data={'msg': 'noAdd', 'checker_id': mission.checker_id})
        return Response(status=status.HTTP_200_OK, data={'msg': 'add', 'checker_id': ''})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def control_mission_status(request):
    mission_id = request.shift_data.data.get('mission_id')
    mission_status = request.shift_data.data.get("mission_status")
    scene_id = request.shift_data.data.get("scene_id")

    if not mission_id:
        raise exceptions.ValidationError("'mission_id':" + error.MISS_PARAMETER)
    if not mission_status:
        raise exceptions.ValidationError("'mission_status':" + error.MISS_PARAMETER)
    if not scene_id and mission_status != constant.MissionStatus.STOP:
        raise exceptions.ValidationError("'scene_id':" + error.MISS_PARAMETER)

    if mission_status == constant.MissionStatus.ISPROCESS:
        SceneMissionManager(scene_id, False).start_mission_check(mission_id)
    elif mission_status == constant.MissionStatus.STOP:
        SceneMissionManager(scene_id, False).stop_mission_check(mission_id)

    return Response(data={'msg': 'success'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def get_params(request):
    mission_id = request.shift_data.data.get('mission_id')
    if mission_id:
        mission = mission_models.Mission.objects.filter(id=mission_id).first()
        if not mission:
            raise exceptions.ValidationError(error.NOT_FOUND)
        if mission.type == constant.Type.CHECK:
            check_mission = mission.checkmission
            params = check_mission.params

            mission_script_path = os.path.join(
                settings.MEDIA_ROOT,
                'scripts/mission/{id}/{script}').format(
                id=mission.id,
                script=check_mission.scripts
            )
            if not os.path.exists(mission_script_path):
                raise Exception('No script file')

            file_object = open(mission_script_path)
            try:
                code_text = file_object.read()
            except Exception:
                code_text = ""
            finally:
                file_object.close()

            data = {
                "id": mission_id,
                "params": params,
                "code_text": code_text
            }
            return Response(data=data, status=status.HTTP_200_OK)
    else:
        raise exceptions.ValidationError(error.MISS_PARAMETER)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def update_mission_params(request):
    mission_id = request.shift_data.data.get('mission_id')
    params = request.shift_data.data.get("params")
    code_text = request.shift_data.data.get("code_text")
    if not mission_id:
        raise exceptions.ValidationError(error.MISS_PARAMETER)

    mission = mission_models.Mission.objects.filter(id=mission_id).first()
    if not mission:
        raise exceptions.ValidationError(error.NOT_FOUND)
    if mission.type == constant.Type.CHECK:
        if hasattr(mission, 'checkmission'):
            mission.checkmission.params = params
            mission.checkmission.save()

            mission_script_path = os.path.join(
                settings.MEDIA_ROOT,
                'scripts/mission/{id}/{script}').format(
                id=mission.id,
                script=mission.checkmission.scripts
            )
            if not os.path.exists(mission_script_path):
                raise Exception('No script file')

            with open(mission_script_path, 'w') as code_file:
                code_file.write(code_text)
                code_file.close()

            return Response(data={'msg': 'success'}, status=status.HTTP_200_OK)
        else:
            raise exceptions.ValidationError(error.NOT_FOUND)

    return Response(data={'msg': 'success'}, status=status.HTTP_200_OK)
