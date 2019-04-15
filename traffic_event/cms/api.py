import os
from django.conf import settings
from django.db import transaction
from rest_framework import viewsets, filters, permissions, exceptions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from base.utils.rest.decorators import request_data
from base_traffic.models import Traffic
from base.utils.rest.mixins import CacheModelMixin, PMixin, DestroyModelMixin
from base_traffic.utils.traffic import copy_traffic
from traffic_event.cms.error import error
from traffic_event.cms.serializers import TrafficEventSerializer, \
    BackgroundTrafficEventSerializer, IntelligentTrafficEventSerializer
from base_traffic.cms import serializers as traffic_serializer
from traffic_event.models import TrafficEvent
from traffic_event.utils.event_data_handle import save_related_traffic
from cr_scene.models import CrScene
from traffic_event.utils.traffic_event_manager import TrafficEventManager

SCRIPT_URL = settings.MEDIA_ROOT + "/traffic/scripts/"


class TrafficEventViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = TrafficEvent.objects.all()
    serializer_class = TrafficEventSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    traffic_type = None

    def get_queryset(self):
        queryset = self.queryset
        return queryset

    def retrieve(self, request, *args, **kwargs):
        traffic_event_id = kwargs.get('pk')
        instance = self.queryset.get(id=traffic_event_id)
        if instance.type == TrafficEvent.Type.BACKGROUND:
            data = BackgroundTrafficEventSerializer(instance).data
        if instance.type == TrafficEvent.Type.INTELLIGENT:
            data = IntelligentTrafficEventSerializer(instance).data

        return Response(data=data)

    def sub_perform_create(self, serializer):
        with transaction.atomic():
            traffic_id = self.request.data.get('traffic')
            traffic = copy_traffic(traffic_id)

            save_related_traffic(self.request, traffic)

            serializer.save(
                traffic=traffic,
                create_user=self.request.user,
                last_edit_user=self.request.user,
            )
            return True

    def sub_perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.instance
            traffic_id = self.request.data.get('traffic')

            if instance.traffic.parent != int(traffic_id) or traffic_id is None:
                traffic = copy_traffic(traffic_id)
            else:
                traffic = instance.traffic

            save_related_traffic(self.request, traffic)

            serializer.save(
                traffic=traffic,
                last_edit_user=self.request.user,
            )
            return True

    def sub_perform_destroy(self, instance):
        instance.status = Traffic.Status.DELETE
        instance.save()
        return True

    @action(methods=['get'], detail=True)
    def get_traffic_test(self, request, pk):
        instance = get_object_or_404(TrafficEvent, pk=pk)
        if instance.type == TrafficEvent.Type.BACKGROUND:
            data = dict(
                loop=instance.traffic.background_traffic.loop,
                multiplier=instance.traffic.background_traffic.multiplier,
                parameter=instance.parameter
            )
        else:
            data = dict(
                suffix=instance.traffic.intelligent_traffic.suffix,
                code=instance.traffic.intelligent_traffic.code,
                parameter=instance.parameter
            )
        return Response(data=data, status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=True)
    def traffic_event_test(self, request, pk):
        with transaction.atomic():
            event = get_object_or_404(TrafficEvent, pk=pk)
            traffic = event.traffic
            data = {}
            fields = ['loop', 'multiplier', 'parameter', 'suffix', 'code']

            for field in fields:
                if field in self.request.data:
                    data.update({field: self.request.data.get(field)})

            if event.type == event.Type.INTELLIGENT:
                code = data.get('code', '')
                script_type = '.py' if int(data.get('suffix')) == 0 else '.sh'
                if not os.path.exists(SCRIPT_URL):
                    os.makedirs(SCRIPT_URL)
                file_path = SCRIPT_URL + traffic.title + script_type
                with open(file_path, 'w') as f:
                    f.write(code)

            if event.type == event.Type.BACKGROUND:
                serializer = traffic_serializer.BackgroundTrafficSerializer(traffic.background_traffic,
                                                                            data=data, partial=True)
            else:
                serializer = traffic_serializer.IntelligentTrafficSerializer(traffic.intelligent_traffic,
                                                                             data=data, partial=True)

            event_serializer = TrafficEventSerializer(event, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            event_serializer.is_valid(raise_exception=True)
            serializer.save(traffic=traffic)
            event_serializer.save()

        return Response(status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False)
    def need_remove_runner(self, request):
        cr_scene_id = self.query_data.get('cr_scene_id', int)
        runner_ids = self.query_data.getlist('runner_id')
        traffic_events = CrScene.objects.get(id=cr_scene_id).traffic_events.filter(status=TrafficEvent.Status.NORMAL)
        runners = [event.runner for event in traffic_events]
        should_removed_runners = [runner for runner in set(runner_ids)
                                  if (runner_ids.count(runner) == runners.count(runner))]

        return Response(status=status.HTTP_200_OK, data=should_removed_runners)

    @action(methods=['GET'], detail=False)
    def need_add_runner(self, request):
        cr_scene_id = self.query_data.get('cr_scene_id', int)
        target_net = self.query_data.get('target_net')
        removed_runner = self.query_data.get('removed_runner')

        traffic = self.query_data.get('traffic', int)
        traffic_obj = Traffic.objects.filter(id=traffic).first()
        if hasattr(traffic_obj, 'background_traffic'):
            machine_id = traffic_obj.background_traffic.trm.id
        if hasattr(traffic_obj, 'intelligent_traffic'):
            machine_id = traffic_obj.intelligent_traffic.tgm.id

        traffic_events = CrScene.objects.get(id=cr_scene_id).traffic_events.filter(status=TrafficEvent.Status.NORMAL)

        if removed_runner:
            traffic_events = traffic_events.exclude(runner=removed_runner)

        for event in traffic_events:
            if target_net == event.target_net:
                if hasattr(event.traffic, 'background_traffic'):
                    if event.traffic.background_traffic.trm.id == machine_id:
                        return Response(data={'msg': 'not_add', 'runner_id': event.runner},
                                        status=status.HTTP_200_OK)
                if hasattr(event.traffic, 'intelligent_traffic'):
                    if event.traffic.intelligent_traffic.tgm.id == machine_id:
                        return Response(data={'msg': 'not_add', 'runner_id': event.runner},
                                        status=status.HTTP_200_OK)

        return Response(status=status.HTTP_200_OK, data={'msg': 'add'})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def manual_traffic(request):
    traffic_event_id = request.shift_data.get('traffic_event_id', int)
    start = request.shift_data.get('start', int)
    scene_id = request.shift_data.get('scene_id', int)

    if traffic_event_id is None:
        raise exceptions.ValidationError(error.MISSING_PARAMETERS)

    if scene_id is None:
        raise exceptions.ValidationError(error.SCENE_NOT_FOUND)

    if traffic_event_id <= 0 or scene_id <= 0:
        raise exceptions.ValidationError(error.INVALID_PARAMETERS)

    traffic_event = TrafficEvent.objects.filter(id=traffic_event_id).first()
    if not traffic_event:
        raise exceptions.ValidationError(error.NOT_FOUND)

    traffifc_manager = TrafficEventManager(traffic_event, scene_id)
    if start:
        _ret = traffifc_manager.start(manual=True)
        if _ret is None:
            raise exceptions.ValidationError(error.CONNECTION_REFUSED)
    else:
        _ret = traffifc_manager.stop()

    if _ret is None or _ret['status'] == 'down':
        raise exceptions.ValidationError(error.CONNECTION_REFUSED)

    elif _ret['status'] != 'ok':
        raise exceptions.ValidationError(error.UNKNOW_ERROR)

    return Response(data={'msg': 'success'}, status=status.HTTP_200_OK)
