# -*- coding: utf-8 -*-
import json
import logging

from django.db.models import Q
from django.utils import timezone

from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PMixin
from base.utils.text import rk
from base.utils.thread import async_exe

from base_cloud import api as cloud
from base_auth.utils.owner import filter_operate_queryset
from base_auth.utils.rest.decorators import owner_queryset
from base_auth.utils.rest.mixins import BatchSetOwnerModelMixin
from base_auth.utils.rest.permissions import check_superuser_permission, check_operate_permission
from base_scene import app_settings
from base_scene.common.standard_device import DeviceHandler
from base_scene.models import (StandardDevice, Network, InstallerType, InstallerResource, Installer,
                               StandardDeviceSnapshot)

from . import consumers as mconsumers
from . import serializers as mserializers
from .error import error


logger = logging.getLogger(__name__)


class StandardDeviceViewSet(BatchSetOwnerModelMixin, DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = StandardDevice.objects.all()
    serializer_class = mserializers.StandardDeviceSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    unlimit_pagination = True

    @owner_queryset
    def get_queryset(self):
        queryset = self.queryset
        image_status = self.query_data.get('image_status', StandardDevice.ImageStatus.values())
        if image_status is not None:
            queryset = queryset.filter(image_status=image_status)

        role = self.query_data.get('role', StandardDevice.Role.values())
        if role is not None:
            queryset = queryset.filter(role=role)

            role_type = self.query_data.get('role_type', StandardDevice.RoleType[role].values())
            if role_type is not None:
                queryset = queryset.filter(role_type=role_type)

        is_real = self.query_data.get('is_real', bool)
        if is_real is not None:
            queryset = queryset.filter(is_real=is_real)

        image_type = self.query_data.get('image_type', StandardDevice.ImageType.values())
        if image_type is not None:
            queryset = queryset.filter(image_type=image_type)

        can_use = self.query_data.get('can_use', bool)
        raw_system_type = self.query_data.get('system_type')
        system_type = self.query_data.get('system_type', StandardDevice.SystemType.values())
        if system_type is not None:
            queryset = queryset.filter(system_type=system_type)
            if can_use:
                queryset = queryset.filter(image_status=StandardDevice.ImageStatus.CREATED)
        elif raw_system_type == 'other':
            queryset = queryset.filter(Q(system_type='') | Q(system_type=None))
        elif raw_system_type == 'all':
            if can_use:
                queryset = queryset.filter(
                    Q(system_type='') | Q(system_type=None) | Q(image_status=StandardDevice.ImageStatus.CREATED)
                )

        system_sub_type = self.query_data.get('system_sub_type', StandardDevice.SystemSubType.values())
        if system_sub_type is not None:
            queryset = queryset.filter(system_sub_type=system_sub_type)

        flavor = self.query_data.get('flavor', StandardDevice.Flavor.values())
        if flavor is not None:
            queryset = queryset.filter(flavor=flavor)

        type = self.query_data.get('type', StandardDevice.Type.values())
        if type is not None:
            queryset = queryset.filter(type=type)

        return queryset

    # 文件上传比较大， 添加validate模式先验证基础数据
    def _validate_mode(self):
        return '_validate' in self.request.data

    def _terminal_mode(self, validated_data, instance=None):
        role = validated_data.get('role')
        role_type = validated_data.get('role_type')
        if instance:
            role = role or instance.role
            role_type = role_type or instance.role_type
        return (role == StandardDevice.Role.TERMINAL
                or (role == StandardDevice.Role.GATEWAY
                    and role_type not in (
                        StandardDevice.RoleGatewayType.ROUTER,
                        StandardDevice.RoleGatewayType.FIREWALL,
                    )))

    def _check_upload_image(self, image_name, disk_format, creating=False):
        if image_name in app_settings.BASE_IMAGE_NAMES:
            raise exceptions.ValidationError({'name': error.CONFLICT_WITH_BASE_IMAGE_NAME})

        if not disk_format:
            raise exceptions.ValidationError({'disk_format': error.INVALID_VALUE})

        image_file = self.request.data.get('image_file')
        third_file_name = self.request.data.get('third_file_name')
        if not image_file and not third_file_name:
            if creating:
                raise exceptions.ValidationError({'image_file': error.INVALID_VALUE})

    def _try_upload_image(self, image_name, image_type, disk_format, meta_data=None):
        image_file = self.request.data.get('image_file')
        third_file_name = self.request.data.get('third_file_name')
        if not image_file and not third_file_name:
            return False

        # 检查镜像是否已存在, 已存在则删除
        image = cloud.image.get(image_name=image_name)
        if image:
            cloud.image.delete(image_name=image_name)

        upload_data = {
            'image_name': image_name,
        }
        if image_file:
            upload_data.update({
                'image_file': image_file,
                'meta_data': {
                    'disk_format': disk_format,
                    'visibility': 'public',
                    'minimum_disk': 0,
                    'minimum_ram': 0,
                }
            })
        else:
            upload_data.update({
                'ftp_file_name': third_file_name,
                'meta_data': {
                    'disk_format': disk_format,
                }
            })

        def created(image):
            logger.info('image[%s] created', image_name)
            StandardDevice.objects.filter(name=image_name).update(image_status=StandardDevice.ImageStatus.CREATED)
            self.clear_cache()
            if meta_data is not None:
                cloud.image.update(image_name=image_name, partial_update=False, **meta_data)
            if image_type == StandardDevice.ImageType.DOCKER:
                cloud.image.local_load_container(image)
            else:
                cloud.image.operator.scene_convert_img_to_disk(image.id)

        def failed(error):
            logger.info('image[%s] failed', image_name)
            StandardDevice.objects.filter(name=image_name).update(image_status=StandardDevice.ImageStatus.ERROR)
            self.clear_cache()

        upload_data.update({
            'created': created,
            'failed': failed,
        })

        cloud.image.create(**upload_data)
        StandardDevice.objects.filter(name=image_name).update(image_status=StandardDevice.ImageStatus.CREATING)
        return True

    def sub_perform_create(self, serializer):
        validated_data = serializer.validated_data

        upload_mode = (self._terminal_mode(validated_data)
                       and not validated_data.get('source_image_name')
                       and not validated_data.get('is_real', False))

        if upload_mode:
            self._check_upload_image(validated_data['name'], validated_data.get('disk_format'), creating=True)

        serializer.save(
            user=self.request.user,
            modify_user=self.request.user,
        )

        if upload_mode:
            # 元数据
            meta_data_str = validated_data.get('meta_data')
            meta_data = json.loads(meta_data_str) if meta_data_str else None
            self._try_upload_image(
                validated_data['name'],
                serializer.instance.image_type,
                validated_data.get('disk_format'),
                meta_data,
            )

        return True

    def sub_perform_update(self, serializer):
        check_operate_permission(self.request.user, serializer.instance)

        instance = serializer.instance
        validated_data = serializer.validated_data
        name = validated_data.get('name')
        is_terminal_mode = self._terminal_mode(validated_data, instance)
        is_real = (('is_real' in validated_data and validated_data.get('is_real'))
                   or ('is_real' not in validated_data and instance.is_real))
        if is_terminal_mode and not is_real and name and name != instance.name:
            async_exe(cloud.image.update, kwargs={'image_name': instance.name, 'name': name})

        upload_mode = (is_terminal_mode
                       and not (validated_data.get('source_image_name') or instance.source_image_name)
                       and not is_real)

        if upload_mode:
            self._check_upload_image(
                validated_data.get('name') or instance.name,
                validated_data.get('disk_format') or instance.disk_format,
            )
            # 待更新元数据
            old_meta_data = serializer.instance.meta_data
            new_meta_data = validated_data.get('meta_data')
        else:
            # 非上传模式无元数据
            validated_data['meta_data'] = None

        serializer.save(
            modify_time=timezone.now(),
            modify_user=self.request.user,
        )

        if upload_mode:
            meta_data_str = new_meta_data or old_meta_data
            meta_data = json.loads(meta_data_str) if meta_data_str else None
            result = self._try_upload_image(validated_data.get('name') or instance.name,
                                            validated_data.get('image_type') or instance.image_type,
                                            validated_data.get('disk_format'), meta_data)
            # 未上传则更新元数据
            if not result and new_meta_data and new_meta_data != old_meta_data:
                cloud.image.update(
                    image_name=serializer.instance.name,
                    partial_update=False,
                    **json.loads(new_meta_data)
                )

        return True

    def sub_perform_destroy(self, instance):
        raise exceptions.PermissionDenied()

    def perform_batch_destroy(self, queryset):
        queryset = filter_operate_queryset(self.request.user, queryset)

        for instance in queryset:
            handler = DeviceHandler(self.request.user, device=instance)
            handler.delete()

        if queryset:
            return True
        return False

    @action(methods=['get', 'post', 'delete'], detail=True)
    def image_scene(self, request, pk=None):
        device = self.get_object()
        check_operate_permission(request.user, device)

        if request.method == 'GET':
            handler = DeviceHandler(request.user, device=device)
            data = handler.get_image_scene()
            return Response(data)
        elif request.method == 'POST':
            handler = DeviceHandler(request.user, device=device)
            handler.create_image_scene(status_updated={
                'func': _image_scene_status_updated,
                'params': {
                    'user_id': request.user.pk,
                    'device_id': device.pk,
                }
            })
            self.clear_cache()
            data = handler.get_image_scene()
            return Response(data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            handler = DeviceHandler(request.user, device=device)
            handler.delete_image_scene()
            self.clear_cache()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def image(self, request, pk=None):
        device = self.get_object()
        check_operate_permission(request.user, device)

        if request.method == 'POST':
            if not device.image_scene:
                raise exceptions.ValidationError(error.DEVICE_NO_SCENE)

            if device.image_status == StandardDevice.ImageStatus.CREATING:
                raise exceptions.ValidationError(error.IMAGE_SAVING)

            device.image_status = StandardDevice.ImageStatus.CREATING
            device.save()
            self.clear_cache()
            mconsumers.StandardDeviceWebsocket.image_status_update(request.user, device.pk)

            name = self.shift_data.get('name')
            desc = self.shift_data.get('desc')

            def created(image):
                StandardDeviceSnapshot.objects.create(
                    standard_device=device,
                    name=name,
                    desc=desc
                )
                self.clear_cache()
                mconsumers.StandardDeviceWebsocket.image_status_update(request.user, device.pk)

            def failed(error):
                self.clear_cache()
                mconsumers.StandardDeviceWebsocket.image_status_update(request.user, device.pk)

            handler = DeviceHandler(request.user, device=device)
            async_exe(handler.create_image, (name, created, failed))

            return Response(status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=True)
    def console_url(self, request, pk=None):
        device = self.get_object()
        check_operate_permission(request.user, device)

        handler = DeviceHandler(request.user, device=device)
        url = handler.get_console_url()
        return Response({'url': url})


class StandardDeviceSnapshotViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = StandardDeviceSnapshot.objects.all()
    serializer_class = mserializers.StandardDeviceSnapshotSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)


def _image_scene_status_updated(user_id, device_id, *args, **kwargs):
    StandardDeviceViewSet.clear_self_cache()
    scene_terminal_id = kwargs.get('scene_terminal_id')
    if scene_terminal_id:
        mconsumers.StandardDeviceWebsocket.scene_status_update(user_id, device_id)


class NetworkViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = Network.objects.all()
    serializer_class = mserializers.NetworkSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def sub_perform_create(self, serializer):
        check_superuser_permission(self.request.user)

        serializer.save(
            user=self.request.user,
            modify_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        check_superuser_permission(self.request.user)

        serializer.save(
            modify_time=timezone.now(),
            modify_user=self.request.user,
        )
        return True

    def sub_perform_destroy(self, instance):
        raise exceptions.PermissionDenied()

    def perform_batch_destroy(self, queryset):
        check_superuser_permission(self.request.user)

        for instance in queryset:
            instance.name = rk()
            instance.status = Network.Status.DELETE
            instance.save()
        if queryset:
            return True
        return False

    @action(methods=['get'], detail=True, permission_classes=[IsAuthenticated])
    def avaliable_ips(self, request, pk=None):
        network = self.get_object()
        ips = cloud.network.get_avaliable_ips(network.net_id, network.cidr)
        return Response(ips, status=status.HTTP_200_OK)


class InstallerTypeViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = InstallerType.objects.all()
    serializer_class = mserializers.InstallerTypeSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('name',)
    ordering = ('name',)
    unlimit_pagination = True

    def sub_perform_create(self, serializer):
        check_superuser_permission(self.request.user)
        return super(InstallerTypeViewSet, self).sub_perform_create(serializer)

    def sub_perform_update(self, serializer):
        check_superuser_permission(self.request.user)
        return super(InstallerTypeViewSet, self).sub_perform_update(serializer)

    def sub_perform_destroy(self, instance):
        raise exceptions.PermissionDenied()

    def perform_batch_destroy(self, queryset):
        check_superuser_permission(self.request.user)

        if queryset.delete() > 0:
            return True
        return False


class InstallerViewSet(BatchSetOwnerModelMixin, DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = Installer.objects.all()
    serializer_class = mserializers.InstallerSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    @owner_queryset
    def get_queryset(self):
        queryset = self.queryset

        type = self.query_data.get('type', int)
        if type is not None:
            queryset = queryset.filter(type=type)

        platform = self.query_data.get('platform', InstallerResource.Platform.values())
        if platform is not None:
            queryset = queryset.filter(resources__platforms__icontains=platform)

        return queryset

    def sub_perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            modify_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        check_operate_permission(self.request.user, serializer.instance)

        serializer.save(
            modify_time=timezone.now(),
            modify_user=self.request.user,
        )
        return True

    def sub_perform_destroy(self, instance):
        raise exceptions.PermissionDenied()

    def perform_batch_destroy(self, queryset):
        queryset = filter_operate_queryset(self.request.user, queryset)

        for instance in queryset:
            instance.name = rk()
            instance.status = Installer.Status.DELETE
            instance.save()
        if queryset:
            return True
        return False
