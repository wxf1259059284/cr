# -*- coding: utf-8 -*-

import json
import os
import pyminizip

from django.conf import settings
from django.db import transaction
from django.utils import six
from rest_framework import exceptions, serializers

from base.utils.text import rk, rk_filename
from base.utils.rest.request import DataFilter
from base.utils.rest.serializers import ModelSerializer

from base_auth.cms.serializers import OwnerSerializer
from base_cloud import api as cloud
from base_scene import app_settings
from base_scene.utils import resource as resource_util
from base_scene.common.util.terminal import system_user_protocols
from base_scene.common.scene_config import SceneConfigHandler
from base_scene.common.standard_device import DeviceHandler
from base_scene.models import (StandardDevice, SceneConfig, SceneTerminal, Disk, Network, InstallerType,
                               InstallerResource, Installer)
from base_scene import models as scene_models

from .error import error


class StandardDeviceSerializer(OwnerSerializer, ModelSerializer):
    image_scene_info = serializers.SerializerMethodField()
    snapshot = serializers.SerializerMethodField()

    _terminal_null_fields = (
        'image_type',
        'system_type',
        'system_sub_type',
        'source_image_name',
        'disk_format',
        'meta_data',
        'image_scene',
        'flavor',
        'access_mode',
        'access_port',
        'access_connection_mode',
        'access_user',
        'access_password',
    )

    def get_image_scene_info(self, obj):
        request = self.context.get('request')
        user = request.user if request else self.context.get('user')
        if user and user == obj.user:
            handler = DeviceHandler(user, device=obj)
            return handler.get_image_scene()
        else:
            return None

    def to_internal_value(self, data):
        data_filter = DataFilter(data)
        if data.get('role'):
            role = data_filter.get('role', StandardDevice.Role.values())
            if not role:
                raise exceptions.ValidationError({'role': error.INVALID_VALUE})
            if data.get('role_type'):
                role_type = data_filter.get('role_type', StandardDevice.RoleType[role].values())
                if role_type is None:
                    raise exceptions.ValidationError({'role_type': error.INVALID_VALUE})

        if data.get('image_type'):
            image_type = data_filter.get('image_type', StandardDevice.ImageType.values())
            if not image_type:
                raise exceptions.ValidationError({'image_type': error.INVALID_VALUE})
        if data.get('system_type'):
            system_type = data_filter.get('system_type', StandardDevice.SystemType.values())
            if not system_type:
                raise exceptions.ValidationError({'system_type': error.INVALID_VALUE})

        if data.get('system_sub_type'):
            system_sub_type = data_filter.get('system_sub_type', StandardDevice.SystemSubType.values())
            if not system_sub_type:
                raise exceptions.ValidationError({'system_sub_type': error.INVALID_VALUE})
            data._mutable = True
            data['system_type'] = StandardDevice.SystemSubTypeMap[system_sub_type]
            data._mutable = False

        if data.get('flavor'):
            flavor = data_filter.get('flavor', StandardDevice.Flavor.values())
            if not flavor:
                raise exceptions.ValidationError({'flavor': error.INVALID_VALUE})
        if data.get('access_mode'):
            access_mode = data_filter.get('access_mode', system_user_protocols)
            if not access_mode:
                raise exceptions.ValidationError({'access_mode': error.INVALID_VALUE})
            if data.get('access_port'):
                if access_mode != SceneTerminal.AccessMode.RDP:
                    data._mutable = True
                    data['access_connection_mode'] = None
                    data._mutable = False

        logo = data.get('logo')
        default_logo = None
        if logo and isinstance(logo, (six.string_types, six.text_type)):
            default_logo_path = os.path.join(app_settings.FULL_DEFAULT_DEVICE_LOGO_DIR, logo)
            if os.path.exists(default_logo_path):
                data._mutable = True
                default_logo = logo
                data.pop('logo')
                data._mutable = False
        ret = super(StandardDeviceSerializer, self).to_internal_value(data)
        if default_logo:
            ret['logo'] = os.path.join(app_settings.DEFAULT_DEVICE_LOGO_DIR, default_logo)

        if data.get('gateway_port_configs'):
            try:
                gateway_port_configs = json.loads(data.get('gateway_port_configs'))
                gateway_port_configs.sort(key=lambda x: x.get('id'))
            except Exception:
                raise exceptions.ValidationError({'gateway_port_configs': error.INVALID_VALUE})
            if not isinstance(gateway_port_configs, list):
                raise exceptions.ValidationError({'gateway_port_configs': error.INVALID_VALUE})
            for port_config in gateway_port_configs:
                if port_config.get('type',
                                   StandardDevice.GatewayPortType.LAN) not in StandardDevice.GatewayPortType.values():
                    port_config['type'] = StandardDevice.GatewayPortType.LAN
            data._mutable = True
            data['gateway_port_configs'] = json.dumps(gateway_port_configs)
            data._mutable = False

        if data.get('meta_data'):
            meta_data_str = data.get('meta_data')
            try:
                meta_data = json.loads(meta_data_str)
            except Exception:
                raise exceptions.ValidationError({'meta_data': error.INVALID_VALUE})
            if not isinstance(meta_data, dict):
                raise exceptions.ValidationError({'meta_data': error.INVALID_VALUE})
            for key in meta_data.keys():
                if not meta_data[key]:
                    meta_data.pop(key)
            data._mutable = True
            data['meta_data'] = json.dumps(meta_data)
            data._mutable = False

        return ret

    # 文件上传比较大， 添加validate模式先验证基础数据
    def _validate_mode(self):
        request = self.context['request']
        return '_validate' in request.data

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

    def create(self, validated_data):
        name = validated_data.get('name')
        if name in app_settings.BASE_IMAGE_NAMES:
            raise exceptions.ValidationError({'name': error.CONFLICT_WITH_BASE_IMAGE_NAME})

        standard_device_type = validated_data.get('type', StandardDevice.Type.NORMAL)
        if StandardDevice.objects.filter(name=name, type=standard_device_type).exists():
            raise exceptions.ValidationError({'name': error.NAME_EXISTS})

        if not validated_data.get('logo'):
            raise exceptions.ValidationError({'logo': error.STANDARD_DEVICE_NO_LOGO})

        if self._terminal_mode(validated_data):
            # 上传模式
            if not validated_data.get('source_image_name'):
                if validated_data.get('disk_format') == 'docker':
                    validated_data['image_type'] = StandardDevice.ImageType.DOCKER
                else:
                    validated_data['image_type'] = StandardDevice.ImageType.VM

            if validated_data.get('is_real'):
                validated_data['image_type'] = StandardDevice.ImageType.REAL
        else:
            [validated_data.update({field: None}) for field in self._terminal_null_fields]

        if self._validate_mode():
            return StandardDevice(**validated_data)
        else:
            return super(StandardDeviceSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        if name in app_settings.BASE_IMAGE_NAMES:
            raise exceptions.ValidationError({'name': error.CONFLICT_WITH_BASE_IMAGE_NAME})

        standard_device_type = instance.type or StandardDevice.Type.NORMAL
        if name and name != instance.name and \
                StandardDevice.objects.filter(name=name, type=standard_device_type).exists():
            raise exceptions.ValidationError({'name': error.NAME_EXISTS})

        if 'logo' in validated_data and validated_data['logo'] is None:
            validated_data.pop('logo')

        if self._terminal_mode(validated_data, instance):
            # 上传模式
            if not (validated_data.get('source_image_name') or instance.source_image_name):
                disk_format = validated_data.get('disk_format') or instance.disk_format
                if disk_format == 'docker':
                    validated_data['image_type'] = StandardDevice.ImageType.DOCKER
                else:
                    validated_data['image_type'] = StandardDevice.ImageType.VM
            # 已有镜像的情况不能更新基础镜像
            if instance.image_status == StandardDevice.ImageStatus.CREATED:
                validated_data.pop('source_image_name', None)

            if ('is_real' in validated_data and validated_data.get('is_real')) \
                    or ('is_real' not in validated_data and instance.is_real):
                validated_data['image_type'] = StandardDevice.ImageType.REAL
        else:
            [validated_data.update({field: None}) for field in self._terminal_null_fields]

        if self._validate_mode():
            return instance
        else:
            return super(StandardDeviceSerializer, self).update(instance, validated_data)

    def get_snapshot(self, obj):
        snapshots = scene_models.StandardDeviceSnapshot.objects.filter(standard_device=obj)
        return StandardDeviceSnapshotSerializer(snapshots, many=True).data

    class Meta:
        model = StandardDevice
        fields = ('id', 'name', 'description', 'logo', 'is_real', 'role', 'role_type',
                  'gateway_port_configs', 'image_type', 'system_type',
                  'system_sub_type', 'source_image_name', 'disk_format', 'meta_data',
                  'image_status', 'error', 'image_scene', 'image_scene_info', 'flavor',
                  'access_mode', 'access_port', 'access_connection_mode', 'access_user',
                  'access_password', 'init_support', 'public_mode', 'user', 'username',
                  'modify_time', 'create_time', 'type', 'snapshot', 'port_map', 'remote_address')
        if settings.DEBUG:
            read_only_fields = ('error', 'image_scene', 'user', 'modify_time', 'create_time')
        else:
            read_only_fields = ('error', 'image_scene', 'user', 'modify_time', 'create_time', 'image_status')


class SceneConfigSerializer(OwnerSerializer, ModelSerializer):
    scene_file = serializers.SerializerMethodField()
    vis_config = serializers.SerializerMethodField()

    # 可获取的file 非debug模式不允许访问file
    def get_scene_file(self, obj):
        if settings.DEBUG:
            return serializers.FileField().to_representation(obj.file)
        else:
            return None

    def get_vis_config(self, obj):
        try:
            return resource_util.convert_json_config(json.loads(obj.json_config))
        except Exception:
            return None

    def _get_initial_scene_file(self):
        return self.initial_data.get('scene_file')

    def _get_context_user(self):
        request = self.context.get('request')
        return request.user if request else self.context.get('user')

    def _parse_json_config(self, data):
        # source_flag json_config来源 0未解析到 1直接传入 2从vis_config 3从资源文件
        source_flag = 0

        # 优先解析json_config
        json_config = data.get('json_config')
        if json_config:
            source_flag = 1
        else:
            # 然后解析资源zip文件中的config.json
            scene_file = data.get('file')
            if scene_file:
                json_config = resource_util.read_json_config_from_file(scene_file)
                if json_config:
                    source_flag = 3

        # 最后解析vis_config
        if not json_config:
            vis_config = self.initial_data.get('vis_config')
            if vis_config:
                try:
                    vis_config = json.loads(vis_config)
                except Exception:
                    pass
                else:
                    json_config = json.dumps(resource_util.convert_vis_config(vis_config))
                    if json_config:
                        source_flag = 2

        # 检查json可解析
        if json_config:
            json.loads(json_config)

        return json_config, source_flag

    def create(self, validated_data):
        try:
            json_config, source_flag = self._parse_json_config(validated_data)
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message or 'invalid config'})
        if not json_config:
            raise exceptions.ValidationError({'json_config': error.NO_SCENE_CONFIG})

        # 需要合并json_config到资源文件
        scene_file = validated_data.get('file')
        if not scene_file:
            scene_file = resource_util.empty_zip_file()
            validated_data['file'] = scene_file

        if source_flag in [1, 2]:
            try:
                validated_data['file'] = resource_util.merge_config_to_file(scene_file, json_config)
            except Exception as e:
                raise exceptions.ValidationError({'file': e.message})

        user = self._get_context_user()
        # handler处理json_config
        validated_data.pop('json_config', None)
        # 创建环境模板
        try:
            handler = SceneConfigHandler(user=user)
            scene_config = handler.create(json_config, **validated_data)
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message})

        return scene_config

    def update(self, instance, validated_data):
        try:
            json_config, source_flag = self._parse_json_config(validated_data)
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message or 'invalid config'})

        # debug模式需要合并json_config到资源文件
        scene_file = validated_data.get('file')
        if (json_config or scene_file) and source_flag != 3:
            # 传入的json没有变化并且没有更新部署文件则不用合并
            if json_config and json_config == instance.json_config and not scene_file:
                pass
            else:
                merging_json_config = json_config if json_config else instance.json_config
                merging_scene_file = (scene_file if scene_file else instance.file) or resource_util.empty_zip_file()
                try:
                    validated_data['file'] = resource_util.merge_config_to_file(merging_scene_file, merging_json_config)
                except Exception as e:
                    raise exceptions.ValidationError({'file': e.message})

        user = self._get_context_user()
        # handler处理json_config
        validated_data.pop('json_config', None)
        # 更新结构
        if json_config:
            try:
                handler = SceneConfigHandler(user=user, scene_config=instance)
                handler.update(json_config, **validated_data)
            except Exception as e:
                raise exceptions.ValidationError({'json_config': e.message})
        # 普通更新
        else:
            for field_name, value in validated_data.items():
                setattr(instance, field_name, value)
            instance.save()

        return instance

    def to_internal_value(self, data):
        internal_data = super(SceneConfigSerializer, self).to_internal_value(data)
        scene_file = self._get_initial_scene_file()
        if scene_file:
            scene_file.name = '%s.zip' % rk()
            internal_data['file'] = scene_file
        return internal_data

    class Meta:
        model = SceneConfig
        if settings.DEBUG:
            fields = ('id', 'type', 'scene_file', 'vis_config', 'json_config', 'name', 'modify_time', 'username')
        else:
            fields = ('id', 'type', 'scene_file', 'vis_config', 'name', 'modify_time', 'username')
        read_only_fields = ('name',)


class DiskSerializer(OwnerSerializer, ModelSerializer):
    mounted = serializers.SerializerMethodField()

    def get_mounted(self, obj):
        return bool(obj.mnt_dir)

    def create(self, validated_data):
        disk = cloud.volume.create(
            name=validated_data['name'],
            size=validated_data['size'],
        )
        validated_data['disk_id'] = disk.id
        return super(DiskSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        raise exceptions.PermissionDenied()

    def to_internal_value(self, data):
        data_filter = DataFilter(data)
        if data.get('format'):
            format = data_filter.get('format', Disk.Format.values())
            if not format:
                raise exceptions.ValidationError({'format': error.INVALID_VALUE})

        return super(DiskSerializer, self).to_internal_value(data)

    class Meta:
        model = Disk
        fields = ('id', 'name', 'size', 'used_size', 'format', 'status', 'user', 'modify_time', 'username', 'mounted')
        read_only_fields = ('user', 'modify_time')


class NetworkSerializer(ModelSerializer):
    def to_internal_value(self, data):
        data_filter = DataFilter(data)

        if data_filter.getlist('dns'):
            dns = data_filter.getlist('dns')
            if not dns:
                raise exceptions.ValidationError({'dns': error.INVALID_VALUE})
            data._mutable = True
            data['dns'] = '|'.join(dns)
            data._mutable = False

        return super(NetworkSerializer, self).to_internal_value(data)

    class Meta:
        model = Network
        fields = ('id', 'name', 'company', 'cidr', 'gateway', 'dns', 'net_id', 'status', 'modify_time')
        read_only_fields = ('modify_time',)


class InstallerTypeSerializer(ModelSerializer):
    class Meta:
        model = InstallerType
        fields = ('id', 'name')


class StandardDeviceSnapshotSerializer(ModelSerializer):
    class Meta:
        model = scene_models.StandardDeviceSnapshot
        fields = ('id', 'name', 'desc', 'create_time')


class InstallerResourceSerializer(ModelSerializer):
    encrypt_file_value = serializers.SerializerMethodField()
    encrypt_filename = serializers.SerializerMethodField()
    encrypt_filesize = serializers.SerializerMethodField()

    file_value = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    filesize = serializers.SerializerMethodField()
    platform_list = serializers.SerializerMethodField()

    def get_encrypt_file_value(self, obj):
        if obj.encrypt_file:
            return obj.encrypt_file.name
        return ''

    def get_encrypt_filename(self, obj):
        if obj.name:
            return '{}.zip'.format(obj.name)

        if obj.encrypt_file:
            filename = os.path.basename(obj.encrypt_file.name)
            return filename
        return ''

    def get_encrypt_filesize(self, obj):
        if obj.encrypt_file:
            filepath = os.path.join(settings.MEDIA_ROOT, obj.encrypt_file.name)
            return os.path.getsize(filepath)
        return 0

    def get_file_value(self, obj):
        if obj.file:
            return obj.file.name
        return ''

    def get_filename(self, obj):
        if obj.name:
            return obj.name

        if obj.file:
            filename = os.path.basename(obj.file.name)
            return filename
        return ''

    def get_filesize(self, obj):
        if obj.file:
            filepath = os.path.join(settings.MEDIA_ROOT, obj.file.name)
            return os.path.getsize(filepath)
        return 0

    def get_platform_list(self, obj):
        if obj.platforms:
            return obj.platforms.split('|')
        return []

    def to_internal_value(self, data):
        data_filter = DataFilter(data)
        if data.get('platform_list'):
            platforms = data_filter.getlist('platform_list', InstallerResource.Platform.values())
            if not platforms:
                raise exceptions.ValidationError({'platform_list': error.INVALID_VALUE})
            if isinstance(data, dict):
                data['platforms'] = '|'.join(platforms)
            else:
                data._mutable = True
                data['platforms'] = '|'.join(platforms)
                data._mutable = False
        return super(InstallerResourceSerializer, self).to_internal_value(data)

    class Meta:
        model = InstallerResource
        fields = ('id', 'platforms', 'name', 'file', 'encrypt_file', 'install_script',
                  'file_value', 'filename', 'filesize', 'encrypt_file_value', 'encrypt_filename',
                  'encrypt_filesize', 'platform_list')
        read_only_fields = ('encrypt_file',)


class InstallerSerializer(OwnerSerializer, ModelSerializer):
    type_name = serializers.SerializerMethodField()
    resource_list = serializers.SerializerMethodField()

    def get_type_name(self, obj):
        if obj.type:
            return obj.type.name
        return None

    def get_resource_list(self, obj):
        return InstallerResourceSerializer(obj.resources.all(), many=True).data

    def create(self, validated_data):
        request = self.context['request']
        resources = json.loads(request.data.get('resources') or '[]')
        with transaction.atomic():
            resource_instances = []
            for resource in resources:
                _uuid = resource['_uuid']
                file = request.data.get('file_' + _uuid)
                if file:
                    resource['name'] = file.name
                    file.name = rk_filename(file.name)
                    resource['file'] = file
                resource_serializer = create_resource(resource)
                resource_instances.append(resource_serializer.instance)
            installer = super(InstallerSerializer, self).create(validated_data)
            installer.resources.add(*resource_instances)
        return installer

    def update(self, instance, validated_data):
        request = self.context['request']
        resources = request.data.get('resources')
        resources = json.loads(resources) if resources else None

        with transaction.atomic():
            installer = super(InstallerSerializer, self).update(instance, validated_data)

            if resources is not None:
                origin_resources = instance.resources.all()
                origin_resource_map = {origin_resource.id: origin_resource for origin_resource in origin_resources}

                new_resource_instances = []
                for resource in resources:
                    r_id = resource.get('id')
                    if r_id:
                        r_id = int(r_id)
                    _uuid = resource.get('_uuid')
                    if not r_id and not _uuid:
                        continue
                    if r_id and r_id not in origin_resource_map.keys():
                        continue

                    if r_id:
                        origin_resource_instance = origin_resource_map.pop(r_id)
                        file = request.data.get('file_%s' % r_id)
                        if file:
                            resource['name'] = file.name
                            file.name = rk_filename(file.name)
                            resource['file'] = file
                        else:
                            resource.pop('file', None)
                        update_resource(origin_resource_instance, resource)
                    else:
                        file = request.data.get('file_' + _uuid)
                        if file:
                            resource['name'] = file.name
                            file.name = rk_filename(file.name)
                            resource['file'] = file
                        resource_serializer = create_resource(resource)
                        new_resource_instances.append(resource_serializer.instance)

                for resource_instance in origin_resource_map.values():
                    resource_instance.file.delete()
                    resource_instance.delete()

                installer.resources.add(*new_resource_instances)
        return installer

    class Meta:
        model = Installer
        fields = ('id', 'name', 'type', 'user', 'modify_time', 'public_mode',
                  'type_name', 'username', 'resource_list')
        read_only_fields = ('user', 'modify_time',)


def create_resource(resource):
    resource_serializer = InstallerResourceSerializer(data=resource)
    resource_serializer.is_valid(raise_exception=True)
    resource_serializer.save()
    if 'file' in resource:
        _encrypt_resouce(resource_serializer.instance)

    return resource_serializer


def update_resource(instance, resource):
    resource_serializer = InstallerResourceSerializer(
        instance,
        data=resource,
        partial=True
    )
    resource_serializer.is_valid(raise_exception=True)
    resource_serializer.save()
    if 'file' in resource:
        _encrypt_resouce(resource_serializer.instance)

    return resource_serializer


def _encrypt_resouce(resource_instance):
    source_file = resource_instance.file
    encrypt_password = rk()
    filename = '{}.zip'.format(rk())
    encrypt_filename = os.path.join('encrypt_installer', filename)
    pyminizip.compress(
        os.path.join(settings.MEDIA_ROOT, source_file.name),
        None,
        os.path.join(settings.MEDIA_ROOT, encrypt_filename),
        encrypt_password,
        5,
    )
    resource_instance.encrypt_file = encrypt_filename
    resource_instance.encrypt_password = encrypt_password
    resource_instance.save()
