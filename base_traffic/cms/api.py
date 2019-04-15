import os

from django.utils import timezone
from rest_framework import viewsets, filters, exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction

from base_traffic.cms.error import TrafficError
from base_traffic.cms.serializers import BackgroundTrafficSerializer, IntelligentTrafficSerializer, TrafficSerializer, \
    BackgroundDataSerializer, IntelligentDataSerializer, TrafficCategorySerializer
from base_traffic.models import Traffic, TrafficCategory
from base.utils.rest.mixins import CacheModelMixin, PMixin, DestroyModelMixin


SCRIPT_URL = settings.MEDIA_ROOT + "/traffic/scripts/"


class TrafficCategoryViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = TrafficCategory.objects.all()
    serializer_class = TrafficCategorySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id',)
    ordering = ('-id',)

    def perform_batch_destroy(self, queryset):
        for instance in queryset:
            if Traffic.objects.filter(category_id=instance.id):
                raise exceptions.ValidationError(TrafficError.CATEGORY_BE_USED)

        if queryset.update(status=TrafficCategory.Status.DELETE) > 0:
            return True
        return False


class TrafficViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = Traffic.objects.all()
    serializer_class = TrafficSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    traffic_type = None

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.request.method == "GET":
            if self.traffic_type == Traffic.Type.BACKGROUND:
                serializer_class = BackgroundDataSerializer
            elif self.traffic_type == Traffic.Type.INTELLIGENT:
                serializer_class = IntelligentDataSerializer

        return serializer_class

    def get_queryset(self):
        if self.action == 'list':
            queryset = self.queryset.exclude(is_copy=True)
        else:
            queryset = self.queryset

        traffic_type = self.traffic_type
        if traffic_type is not None:
            queryset = queryset.filter(type=traffic_type)

        query_traffic_type = self.query_data.get('type', int)
        if query_traffic_type:
            queryset = queryset.filter(type=query_traffic_type)

        category = self.query_data.get('category', int)
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def sub_perform_create(self, serializer):
        serializer.save(
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = Traffic.Status.DELETE
        instance.save()
        return True


class BackgroundTrafficViewSet(TrafficViewSet):
    traffic_type = Traffic.Type.BACKGROUND

    def retrieve(self, request, *args, **kwargs):
        traffic_id = kwargs.get('pk')
        instance = self.queryset.get(id=traffic_id)
        data = BackgroundDataSerializer(instance).data

        return Response(data=data)

    def sub_perform_create(self, serializer):
        with transaction.atomic():
            super(BackgroundTrafficViewSet, self).sub_perform_create(serializer)
            traffic = serializer.instance

            background_data = {}
            fields = ['pcap_file', 'loop', 'mbps', 'multiplier', 'file_name', 'trm']

            for field in fields:
                if field in self.request.data:
                    background_data.update({field: self.request.data.get(field)})

            if self.request.data.get('trm') is None or self.request.data.get('trm') == '':
                raise exceptions.ValidationError({'trm': [TrafficError.REQUIRED_FIELD]})

            if self.request.data.get('category') is None or self.request.data.get('category') == '':
                raise exceptions.ValidationError({'category': [TrafficError.REQUIRED_FIELD]})

            background_serializer = BackgroundTrafficSerializer(data=background_data)
            background_serializer.is_valid(raise_exception=True)
            background_serializer.save(traffic=traffic)

            serializer.save(
                type=self.traffic_type,
                create_user=self.request.user,
                last_edit_user=self.request.user,
            )

            return True

    def sub_perform_update(self, serializer):
        with transaction.atomic():
            super(BackgroundTrafficViewSet, self).sub_perform_update(serializer)
            traffic = serializer.instance
            background_data = {}
            fields = ['loop', 'mbps', 'multiplier', 'file_name', 'trm']

            for field in fields:
                if field in self.request.data:
                    background_data.update({field: self.request.data.get(field)})

            if hasattr(self.request.data.get('pcap_file'), 'file'):
                background_data['pcap_file'] = self.request.data.get('pcap_file')

            background_serializer = BackgroundTrafficSerializer(traffic.background_traffic, data=background_data,
                                                                partial=True)
            background_serializer.is_valid(raise_exception=True)
            background_serializer.save(traffic=traffic)
            serializer.save(
                last_edit_user=self.request.user,
            )

            return True


class IntelligentTrafficViewSet(TrafficViewSet):
    traffic_type = Traffic.Type.INTELLIGENT

    def retrieve(self, request, *args, **kwargs):
        traffic_id = kwargs.get('pk')
        instance = self.queryset.get(id=traffic_id)
        data = IntelligentDataSerializer(instance).data

        return Response(data=data)

    def sub_perform_create(self, serializer):
        with transaction.atomic():
            super(IntelligentTrafficViewSet, self).sub_perform_create(serializer)
            traffic = serializer.instance

            code = self.request.data.get('code', '')
            script_type = '.py' if int(self.request.data.get('suffix')) == 0 else '.sh'
            if not os.path.exists(SCRIPT_URL):
                os.makedirs(SCRIPT_URL)
            file_path = SCRIPT_URL + self.request.data.get('title') + script_type
            with open(file_path, 'w') as f:
                f.write(code)

            if self.request.data.get('file_name') is None:
                raise exceptions.ValidationError({'file_name': [TrafficError.REQUIRED_FIELD]})
            else:
                file_name = self.request.data.get('file_name')

            if self.request.data.get('suffix') is None:
                raise exceptions.ValidationError({'suffix': [TrafficError.REQUIRED_FIELD]})
            else:
                suffix = self.request.data.get('suffix')

            if self.request.data.get('tgm') is None:
                raise exceptions.ValidationError({'tgm': [TrafficError.REQUIRED_FIELD]})
            else:
                tgm_id = self.request.data.get('tgm')

            intelligent_data = {
                'code': code,
                'file_name': file_name,
                'suffix': suffix,
                'tgm': tgm_id
            }

            intelligent_serializer = IntelligentTrafficSerializer(data=intelligent_data)
            intelligent_serializer.is_valid(raise_exception=True)
            intelligent_serializer.save(traffic=traffic)

            serializer.save(
                type=self.traffic_type,
                create_user=self.request.user,
                last_edit_user=self.request.user,
            )

            return True

    def sub_perform_update(self, serializer):
        with transaction.atomic():
            super(IntelligentTrafficViewSet, self).sub_perform_update(serializer)
            traffic = serializer.instance
            intelligent_data = {}
            fields = ['code', 'suffix', 'file_name', 'tgm']

            for field in fields:
                if field in self.request.data:
                    intelligent_data.update({field: self.request.data.get(field)})

            if 'code' in intelligent_data or 'suffix' in intelligent_data:
                suffix = int(intelligent_data.get('suffix')) if 'suffix' in intelligent_data \
                                                                else traffic.intelligent_traffic.suffix
                code = intelligent_data.get('code') if 'code' in intelligent_data else traffic.intelligent_traffic.code
                script_type = '.py' if suffix == 0 else '.sh'
                title = intelligent_data['title'] if intelligent_data.get('title') else traffic.title
                if not os.path.exists(SCRIPT_URL):
                    os.makedirs(SCRIPT_URL)
                file_path = SCRIPT_URL + title + script_type
                with open(file_path, 'w') as f:
                    f.write(code)

            intelligent_serializer = IntelligentTrafficSerializer(traffic.intelligent_traffic, data=intelligent_data,
                                                                  partial=True)
            intelligent_serializer.is_valid(raise_exception=True)
            intelligent_serializer.save(traffic=traffic)

            serializer.save(
                last_edit_user=self.request.user,
            )

            return True
