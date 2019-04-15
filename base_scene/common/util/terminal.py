# -*- coding: utf-8 -*-
import json
import logging
import re
import time

from django.conf import settings
from django.utils import six, timezone
from django.db.models import Q

from base.utils import udict
from base.utils.enum import Enum
from base.utils.functional import cached_property
from base.utils.models.common import get_obj
from base.utils.network import probe
from base.utils.text import rk

from base_cloud import api as cloud
from base_proxy import app_settings as proxy_settings
from base_proxy import api as proxy
from base_remote.managers import RemoteManager, MonitorManager

from base_scene import app_settings
from base_scene.common.error import error
from base_scene.common.exceptions import SceneException
from base_scene.models import StandardDevice, SceneTerminal, Installer
from base_scene.utils import common
from base_scene.utils.docker import create_docker_lock

from .installer import generate_install_script
from .node import NodeUtil


logger = logging.getLogger(__name__)


ip_pattern = re.compile(r'^\w+\.ip$')


ip_type = Enum(
    INNER_FIXED=0,
    OUTER_FIXED=1,
    FLOAT=2,
)

creating_status = (
    SceneTerminal.Status.CREATING,
    SceneTerminal.Status.HATCHING,
    SceneTerminal.Status.STARTING,
    SceneTerminal.Status.DEPLOYING,
)

process_status = (
    SceneTerminal.Status.CREATING,
    SceneTerminal.Status.HATCHING,
    SceneTerminal.Status.STARTING,
    SceneTerminal.Status.DEPLOYING,
    SceneTerminal.Status.RUNNING,
    SceneTerminal.Status.PAUSE,
)

using_status = (
    SceneTerminal.Status.RUNNING,
    SceneTerminal.Status.PAUSE,
)

end_status = (
    SceneTerminal.Status.DELETED,
    SceneTerminal.Status.ERROR,
    SceneTerminal.Status.RUNNING,
    SceneTerminal.Status.PAUSE,
)

system_user_protocols = (
    SceneTerminal.AccessMode.SSH,
    SceneTerminal.AccessMode.RDP,
    SceneTerminal.AccessMode.CONSOLE,
)

remote_protocols = (
    SceneTerminal.AccessMode.SSH,
    SceneTerminal.AccessMode.RDP
)


class PropertyMixin(object):

    node_model = SceneTerminal

    @cached_property
    def standard_device(self):
        return StandardDevice.objects.filter(
            Q(standarddevicesnapshot__name=self.node.image) | Q(name=self.node.image)
        ).first()

    @cached_property
    def init_support(self):
        if self.standard_device:
            return self.standard_device.init_support
        else:
            base_image = app_settings.BASE_IMAGE_MAPPING.get(self.node.image)
            return base_image['init_support'] if base_image else False

    @cached_property
    def hang_info(self):
        return get_terminal_hang_info(self.node)

    @cached_property
    def ip_type(self):
        return get_terminal_ip_type(self.node, self.hang_info)

    @cached_property
    def external_net(self):
        return get_terminal_external_net(self.node)

    @cached_property
    def can_access_externel(self):
        return can_terminal_access_externel(self.node)

    @cached_property
    def system_users(self):
        user_dict = {}
        access_modes = json.loads(self.node.access_modes)
        for access_mode in access_modes:
            if access_mode['protocol'] in system_user_protocols:
                username = access_mode.get('username')
                if username and username not in user_dict:
                    password = access_mode.get('password', '')
                    user_dict[username] = {
                        'username': username,
                        'password': password,
                    }
        return user_dict.values()

    @cached_property
    def installers(self):
        return Installer.objects.filter(name__in=json.loads(self.node.installers))

    @cached_property
    def installer_script(self):
        if self.standard_device and self.installers:
            return generate_install_script(self.standard_device, self.installers)
        else:
            return None

    @cached_property
    def custom_script(self):
        return (self.node.custom_script or '') + (self.installer_script or '')

    @cached_property
    def remote_manager(self):
        return RemoteManager(self.user, host=self.node.host_ip)

    @property
    def can_access(self):
        return can_access_terminal(self.node, self.standard_device)

    @property
    def access_info(self):
        return get_terminal_access_info(self.node, self.standard_device)

    @property
    def access_infos(self):
        return get_terminal_access_infos(self.node, self.standard_device)


class UtilMixin(object):

    # 探测检查机器状态
    def check_status(self, created):
        # if self.init_support:
        #     self.timout_check_status(created)
        # else:
        self.probe_check_status(created)

    # 检查机器状态
    def probe_check_status(self, created, limit_time=app_settings.CHECK_TERMINAL_TIMEOUT, step_time=1):
        scene_terminal = self.node

        protocol, ip, port = self.access_info
        if not ip:
            created()
            return

        def stop_check():
            last_status = self.get_latest_status()
            return last_status in end_status

        probe(
            ip,
            port=port,
            limit_time=limit_time,
            step_time=step_time,
            stop_check=stop_check,
            log_prefix='terminal[%s] status' % scene_terminal.id,
            callback=created,
            timeout_callback=created
        )

    # 超时检查
    def timout_check_status(self, created, limit_time=app_settings.CHECK_TERMINAL_TIMEOUT, step_time=1):
        scene_terminal = self.node

        all_time = 0
        while True:
            logger.info('timout check - terminal[%s] status: %ss' % (scene_terminal.id, all_time))
            last_status = self.get_latest_status()
            if last_status in end_status:
                break
            else:
                if all_time >= limit_time:
                    try:
                        created()
                    except Exception:
                        pass
                    break
                else:
                    time.sleep(step_time)
                    all_time += step_time

    # 解析脚本参数
    def parse_script_val(self, val, sub_id_net=None):
        scene_terminal = self.node

        if val == 'PLATFORM_IP':
            return settings.SERVER_IP
        elif val == 'PLATFORM_PORT':
            return settings.SERVER_PORT
        elif ip_pattern.match(val):
            if not sub_id_net:
                raise SceneException(error.PARSE_SERVER_SCRIPT_VAL_ERROR(id=scene_terminal.name, val=val))
            parts = val.spilt('.')
            if len(parts) not in (2, 3):
                raise SceneException(error.PARSE_SERVER_SCRIPT_VAL_ERROR(id=scene_terminal.name, val=val))
            terminal_sub_id = parts[0]
            if terminal_sub_id not in sub_id_net:
                raise SceneException(error.PARSE_SERVER_SCRIPT_VAL_ERROR(id=scene_terminal.name, val=val))
            net_info = sub_id_net[terminal_sub_id]
            if len(parts) == 2:
                return net_info.values()[0]
            else:
                net_sub_id = parts[1]
                if net_sub_id not in net_info:
                    raise SceneException(error.PARSE_SERVER_SCRIPT_VAL_ERROR(id=scene_terminal.name, val=val))
                return net_info[net_sub_id]
        else:
            return val

    # 解析脚本
    def parse_script(self, script, sub_id_net=None):
        if not script:
            return script
        parts = script.split(' ')
        parsed_parts = []
        for part in parts:
            if not part:
                continue
            if part.startswith('{') and part.endswith('}'):
                parsed_part = self.parse_script_val(part[1:-1], sub_id_net)
            else:
                parsed_part = part
            parsed_parts.append(parsed_part)

        return ' '.join(parsed_parts)

    def add_ssh_connection(self, hostname, port=22, username=None, password=None, private_key=None):
        connection_name = '%s:%s:%s:%s' % (self.user.id, hostname, port, rk())
        kwargs = {
            'port': port
        }
        if username:
            kwargs['username'] = username
        if password:
            kwargs['password'] = password
        if private_key:
            kwargs['private_key'] = private_key
        try:
            connection = self.remote_manager.create_ssh_connection(connection_name, hostname, **kwargs)
        except Exception as e:
            logger.error('add ssh connection error: %s' % e)
            return None

        return connection.connection_id

    def add_rdp_connection(self, hostname, port=3389, username=None, password=None, security=None, system_type=None):
        connection_name = '%s:%s:%s:%s' % (self.user.id, hostname, port, rk())
        kwargs = {
            'port': port
        }
        if username:
            kwargs['username'] = username
        if password:
            kwargs['password'] = password
        if security:
            kwargs['security'] = security

        if system_type and system_type == SceneTerminal.SystemType.LINUX:
            kwargs['enable-sftp'] = 'true'

        try:
            connection = self.remote_manager.create_rdp_connection(connection_name, hostname, **kwargs)
        except Exception as e:
            logger.error('add rdp connection error: %s' % e)
            return None

        return connection.connection_id

    def remove_connection(self, connection_id):
        try:
            self.remote_manager.remove_connection(connection_id)
        except Exception as e:
            logger.error('remove connection error: %s' % e)


class ControlMixin(object):

    def change_tunnel(self, tunnel):
        scene_terminal = self.node

        tunnel_mapping = {tunnel_info['id']: tunnel_info for tunnel_info in app_settings.TUNNELS}
        if tunnel not in tunnel_mapping.keys():
            raise SceneException(error.INVALID_TUNNEL)

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.vm.change_tunnel(scene_terminal.server_id, tunnel)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.docker.change_tunnel(scene_terminal.server_id, tunnel)

        self.update_node({'tunnel': tunnel})

    def attach_disk(self, disk_ids):
        scene_terminal = self.node

        if isinstance(disk_ids, six.string_types):
            disk_ids = [disk_ids]

        volumes = json.loads(scene_terminal.volumes)
        need_save = False
        for disk_id in disk_ids:
            try:
                common.attach_disk(scene_terminal.server_id, disk_id)
            except Exception as e:
                logger.error('terminal[%s] attach disk[%s] error: %s', scene_terminal.name, disk_id, e)
            else:
                if disk_id not in volumes:
                    volumes.append(disk_id)
                    need_save = True

        if need_save:
            scene_terminal.volumes = json.dumps(volumes)
            scene_terminal.save()

    def detach_disk(self, disk_ids):
        scene_terminal = self.node

        if isinstance(disk_ids, six.string_types):
            disk_ids = [disk_ids]

        volumes = json.loads(scene_terminal.volumes)
        need_save = False
        for disk_id in disk_ids:
            try:
                common.detach_disk(scene_terminal.server_id, disk_id)
            except Exception as e:
                logger.error('terminal[%s] detach disk[%s] error: %s', scene_terminal.name, disk_id, e)
            else:
                if disk_id in volumes:
                    volumes.remove(disk_id)
                    need_save = True

        if need_save:
            scene_terminal.volumes = json.dumps(volumes)
            scene_terminal.save()

    def pause(self):
        scene_terminal = self.node

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.vm.pause(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.docker.pause(scene_terminal.server_id, local=self.scene_util.is_local,
                                   host=scene_terminal.host_ip)

    def recover(self):
        scene_terminal = self.node

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.vm.unpause(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.docker.unpause(scene_terminal.server_id, local=self.scene_util.is_local,
                                     host=scene_terminal.host_ip)

    def start(self):
        scene_terminal = self.node

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.vm.start(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.docker.start(scene_terminal.server_id, local=self.scene_util.is_local,
                                   host=scene_terminal.host_ip)

    def stop(self):
        scene_terminal = self.node

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.vm.stop(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.docker.stop(scene_terminal.server_id, local=self.scene_util.is_local, host=scene_terminal.host_ip)

    def restart(self):
        scene_terminal = self.node

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.vm.restart(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.docker.restart(scene_terminal.server_id, local=self.scene_util.is_local,
                                     host=scene_terminal.host_ip)

    def save_image(self, image_name, created=None, failed=None):
        scene_terminal = self.node

        def image_created(image):
            self.start()

            if created:
                created(image)

        def image_failed(error):
            self.start()

            if failed:
                failed(error)

        if self.scene_util.is_local:
            image_failed(error.LOCAL_CONTAINER_NOT_SUPPORT_IMAGE)
            return

        if scene_terminal.status not in using_status:
            image_failed(error.TERMINAL_NOT_READY)
            return

        try:
            # 删除旧的镜像
            cloud.image.delete(image_name=image_name)
            self.stop()
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                cloud.image.create(image_name, vm_id=scene_terminal.server_id, created=image_created,
                                   failed=image_failed)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                cloud.image.create(image_name, container_id=scene_terminal.server_id, created=image_created,
                                   failed=image_failed)
        except Exception as e:
            if failed:
                failed(e.message)


class GetMixin(object):

    def get_data(self, fields=None):
        scene_terminal = self.node

        data = {
            'id': scene_terminal.id,
            'sub_id': scene_terminal.sub_id,
            'name': scene_terminal.name,
            'status': scene_terminal.status,
            'error': scene_terminal.error,
            'fixed_ips': [],
            'float_ip': scene_terminal.float_ip,
            'proxy_ip': proxy_settings.PROXY_IP if self.proxy else None,
            'proxy_port': json.loads(scene_terminal.proxy_port),
            'host_ip': scene_terminal.host_ip,
            'host_proxy_port': json.loads(scene_terminal.host_proxy_port),
            'access_mode': {},
            'tunnel': scene_terminal.tunnel,
            'extra': scene_terminal.extra,
        }

        if udict.need_field('access_mode', fields):
            access_modes = json.loads(scene_terminal.access_modes)
            access_mode_map = {get_access_mode_key(mode): mode for mode in access_modes}

            if self.remote:
                self._ensure_remote_connection(access_mode_map)
                for access_mode_key, access_mode in access_mode_map.items():
                    connection = access_mode.pop('connections', {}).get(str(self.user.id), {})
                    connection_id = connection.get('connection_id')
                    if connection_id:
                        if access_mode['protocol'] == SceneTerminal.AccessMode.SSH:
                            access_mode['connection_url'] = self.remote_manager.get_ssh_connection_url(connection_id)
                        elif access_mode['protocol'] == SceneTerminal.AccessMode.RDP:
                            access_mode['connection_url'] = self.remote_manager.get_rdp_connection_url(connection_id)

            data['access_mode'] = access_mode_map

        if udict.need_field('fixed_ips', fields):
            net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
            fixed_ips = [net_config.get('ip') for net_config in net_configs if net_config.get('ip')]
            data['fixed_ips'] = fixed_ips

        if udict.need_field('nat_info', fields):
            nat_info = {}
            try:
                float_ip_params = json.loads(scene_terminal.float_ip_params)
                if float_ip_params:
                    nat_info.update({
                        'route_net': float_ip_params.get('route_net'),
                        'fixed_ip': float_ip_params['fixed_ip'],
                        'float_ip': scene_terminal.float_ip,
                    })
            except Exception:
                pass
            data['nat_info'] = nat_info

        if udict.need_field('remote_address', fields) and scene_terminal.is_real and self.standard_device:
            data['remote_address'] = self.standard_device.remote_address

        if scene_terminal.status in creating_status:
            if udict.need_field('loaded_seconds', fields) or udict.need_field('estimate_remain_seconds', fields):
                loaded_seconds, remain_seconds = self.get_process_seconds()
                data['loaded_seconds'] = loaded_seconds
                data['estimate_remain_seconds'] = remain_seconds
        elif scene_terminal.status in using_status:
            running_time = timezone.now() - (scene_terminal.created_time or scene_terminal.create_time)
            data['running_seconds'] = int(running_time.total_seconds())

        return udict.filter_data(data, fields)

    def _ensure_remote_connection(self, access_mode_map):
        scene_terminal = self.node

        access_modes = json.loads(scene_terminal.access_modes)
        host_proxy_port_mapping = json.loads(scene_terminal.host_proxy_port)
        need_update = False
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            if protocol not in remote_protocols or not access_mode.get('username'):
                continue

            access_mode_key = get_access_mode_key(access_mode)
            if access_mode_key not in access_mode_map:
                continue

            ip, port = get_ip_port_for_remote(scene_terminal, access_mode, host_proxy_port_mapping)
            if not ip:
                continue

            connections = access_mode.get('connections', {})
            connection = connections.get(str(self.user.id), {})
            if not connection:
                if protocol == SceneTerminal.AccessMode.SSH:
                    connection['connection_id'] = self.add_ssh_connection(
                        ip,
                        port,
                        access_mode['username'],
                        access_mode.get('password', '')
                    )
                    need_update = True
                elif protocol == SceneTerminal.AccessMode.RDP:
                    rdp_params = {
                        'hostname': ip,
                        'port': port,
                        'username': access_mode['username'],
                        'password': access_mode.get('password', ''),
                        'system_type': scene_terminal.system_type,
                    }
                    security = access_mode.get('mode')
                    if security:
                        rdp_params['security'] = security
                    connection['connection_id'] = self.add_rdp_connection(**rdp_params)
                    need_update = True
                connections[str(self.user.id)] = connection

            access_mode['connections'] = connections
            access_mode_map[access_mode_key]['connections'] = connections

        if need_update:
            self.update_node({'access_modes': json.dumps(access_modes)})

    # 获取最新状态
    def get_latest_status(self, status=None):
        scene_terminal = self.node

        try:
            latest_status = SceneTerminal.objects.filter(pk=scene_terminal.pk).values('status')[0]['status']
        except Exception:
            latest_status = scene_terminal.status

        if status is not None and latest_status in process_status and status in process_status:
            if latest_status > status:
                latest_status = status
        return latest_status

    def get_estimate_consume_time(self):
        scene_terminal = self.node

        similar_terminal = SceneTerminal.objects.filter(
            consume_time__gt=0,
            image=scene_terminal.image,
            install_script=scene_terminal.install_script,
            init_script=scene_terminal.init_script
        ).order_by('-create_time').first()
        consume_time = similar_terminal.consume_time if similar_terminal else None
        return consume_time

    # 获取预估的机器创建消耗时间
    def get_process_seconds(self):
        scene_terminal = self.node

        consume_time = self.get_estimate_consume_time()
        return common.get_part_seconds(scene_terminal.create_time, consume_time)

    def get_console_url(self):
        scene_terminal = self.node

        if (scene_terminal.is_real
                or not scene_terminal.server_id
                or not scene_terminal.image_type == SceneTerminal.ImageType.VM):
            return None
        url = cloud.vm.get_console_url(scene_terminal.server_id)
        return url

    def get_all_remote_info(self):
        scene_terminal = self.node

        remote_info = {}
        access_modes = json.loads(scene_terminal.access_modes)
        for access_mode in access_modes:
            if access_mode['protocol'] in remote_protocols:
                connections = access_mode.get('connections', {})
                for user_id, connection in connections.items():
                    connection_id = connection.get('connection_id')
                    if connection_id:
                        remote_info[user_id] = connection_id
        return remote_info

    def _get_connection_id(self):
        scene_terminal = self.node

        access_modes = json.loads(scene_terminal.access_modes)
        for access_mode in access_modes:
            if access_mode['protocol'] in remote_protocols:
                connections = access_mode.get('connections', {})
                connection = connections.get(str(self.user.id), {})
                connection_id = connection.get('connection_id')
                if connection_id:
                    return connection_id

        return None

    def get_monitor_url(self):
        scene_terminal = self.node

        connection_id = self._get_connection_id()
        if not connection_id:
            return None

        manager = MonitorManager(host=scene_terminal.host_ip)
        ret = manager.share_active_sessions_for_monitor(connection_ids=[connection_id])
        for connection_id, url in ret.items():
            return url

        return None

    def get_assistance_url(self):
        scene_terminal = self.node

        connection_id = self._get_connection_id()
        if not connection_id:
            return None

        manager = MonitorManager(host=scene_terminal.host_ip)
        ret = manager.share_active_sessions_for_assistance(connection_ids=[connection_id])
        for connection_id, url in ret.items():
            return url

        return None

    def get_net_config(self, net_sub_id):
        scene_terminal = self.node

        net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
        net_config_dict = {net_config['id']: net_config for net_config in net_configs}
        return net_config_dict.get(net_sub_id)


class CreateMixin(object):

    def fix_create_prefer(self):
        standard_device = self.standard_device
        scene_terminal = self.node
        if standard_device:
            if scene_terminal.system_type != standard_device.system_type:
                scene_terminal.system_type = standard_device.system_type
            if scene_terminal.system_sub_type != standard_device.system_sub_type:
                scene_terminal.system_sub_type = standard_device.system_sub_type
            if scene_terminal.image_type != standard_device.image_type:
                scene_terminal.image_type = standard_device.image_type
            if scene_terminal.flavor < standard_device.flavor:
                scene_terminal.flavor = standard_device.flavor

    def prepare_network(self, ran_ips=None, float_ip_info=None, external_port_info=None):
        scene_terminal = self.node

        # 准备网络参数
        networks = []
        net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
        net_config_dict = {net_config['id']: net_config for net_config in net_configs}
        nets = scene_terminal.nets.all()
        float_ip = float_ip_info[0] if float_ip_info else None
        external_ip = external_port_info[0] if external_port_info else None
        for net in nets:
            network = None
            net_config = None
            is_external = common.is_external_net(net.sub_id)
            # 直连外网
            if is_external:
                if not external_port_info:
                    raise SceneException(error.NO_ENOUGH_EXTERNAL_NET_PORT)
                network = {'port_id': external_port_info[1]}
                if net.sub_id in net_config_dict:
                    net_config = net_config_dict[net.sub_id]
                    net_config['ip'] = external_ip
                else:
                    net_configs.append({'id': net.sub_id, 'ip': external_ip})
            else:
                has_ip = False
                if net.sub_id in net_config_dict:
                    net_config = net_config_dict[net.sub_id]
                    ip = net_config.get('ip')
                    if ip:
                        network = {'net_id': net.net_id, 'fixed_ip': ip}
                        has_ip = True
                else:
                    net_config = {
                        'id': net.sub_id,
                        'ip': ''
                    }
                    net_configs.append(net_config)
                if not has_ip:
                    ip = ran_ips[net.sub_id].pop(0)
                    network = {'net_id': net.net_id, 'fixed_ip': ip}
                    net_config['ip'] = ip

            if network:
                if net_config:
                    network['gateway_port_id'] = net_config.get('gateway_port_id')
                networks.append(network)

        # 没有连接任何网络默认连接到外网上
        if external_ip and len(nets) == 0:
            networks.append({'port_id': external_port_info[1]})

        # 外部引用网络信息
        hang_access_ip = None
        if self.hang_info:
            networks.append({
                'net_id': self.hang_info['network_id'],
                'fixed_ip': self.hang_info['fixed_ip']
            })
            if self.hang_info.get('can_access'):
                hang_access_ip = self.hang_info['fixed_ip']

        # networks排序
        networks.sort(key=lambda x: x.get('gateway_port_id'))
        for network in networks:
            network.pop('gateway_port_id', None)

        net_ports = []
        # 预分配网络端口
        for network in networks:
            net_id = network.pop('net_id', None)
            fixed_ip = network.pop('fixed_ip', None)
            if net_id and fixed_ip:
                try:
                    port_map = cloud.network.preallocate_ports(net_id, pre_ips=[fixed_ip])
                    if not port_map:
                        raise SceneException(error.NO_ENOUGH_IP)
                except Exception as e:
                    for net_port in net_ports:
                        try:
                            cloud.network.delete_port(net_port)
                        except Exception:
                            pass
                    raise e

                port_id = port_map.values()[0]
                network['port_id'] = port_id
                net_ports.append(port_id)

        if external_port_info:
            net_ports.append(external_port_info[1])

        float_ip_params = {}
        if float_ip:
            fixed_ip = None
            network_id = None
            route_net_sub_id = None
            # 默认分配浮动ip
            if self.external_net:
                if not common.is_external_net(self.external_net.sub_id):
                    net_sub_id_ip = {net_config['id']: net_config['ip'] for net_config in net_configs}
                    fixed_ip = net_sub_id_ip[self.external_net.sub_id]
                    network_id = self.external_net.net_id
                    route_net_sub_id = self.external_net.sub_id
            # 统一的外网分配浮动ip
            elif self.hang_info and self.hang_info.get('allocate_float_ip'):
                fixed_ip = self.hang_info['fixed_ip']
                network_id = self.hang_info['network_id']

            if fixed_ip and network_id:
                float_ip_params.update({
                    'network_id': network_id,
                    'fixed_ip': fixed_ip,
                    'float_ip_info': float_ip_info,
                })
                if route_net_sub_id:
                    float_ip_params['route_net'] = route_net_sub_id

        return {
            'networks': networks,
            'net_configs': net_configs,
            'float_ip_params': float_ip_params,
            'float_ip': float_ip or external_ip or hang_access_ip,
            'net_ports': net_ports
        }

    def prepare_install(self):
        volumes = []
        if self.hang_info:
            volumes = self.hang_info.get('volumes', [])

        return {
            'volumes': volumes,
        }

    def prepare_create_params(self, resource_name=None, networks=None, report_started=None, report_inited=None,
                              attach_url=None):
        scene_terminal = self.node

        image_name = scene_terminal.image
        try:
            image = cloud.image.get(image_name=scene_terminal.image)
        except Exception:
            image = None

        if not image and scene_terminal.image_type == SceneTerminal.ImageType.VM:
            try:
                image = cloud.volume.get(snapshot_name=scene_terminal.image)
            except Exception:
                image = None

        if not image:
            image_name = self.standard_device.source_image_name if self.standard_device else image_name
            logger.info('[%s]terminal(%s) try use source image: %s', scene_terminal.id, scene_terminal.name, image_name)

        create_params = {
            'name': resource_name or scene_terminal.name,
            'image': image_name,
            'system_type': scene_terminal.system_type,
            'flavor': scene_terminal.flavor,
            'attach_url': attach_url,
            'networks': networks or [],
            'custom_script': self.custom_script,
            'install_script': scene_terminal.install_script,
            'init_script': scene_terminal.init_script,
        }
        if self.init_support:
            create_params['users'] = self.system_users

        if scene_terminal.image_type == SceneTerminal.ImageType.VM and scene_terminal.float_ip:
            if report_started:
                create_params['report_started'] = report_started
            if report_inited:
                create_params['report_inited'] = report_inited

        return create_params

    def create_server(self, create_params):
        scene_terminal = self.node

        if scene_terminal.image_type == SceneTerminal.ImageType.VM:
            create_params = cloud.vm.load_create_params(**create_params)
            server = cloud.vm.send_create(**create_params)
            status = self.get_latest_status(SceneTerminal.Status.HATCHING)
            if status == SceneTerminal.Status.HATCHING:
                self.update_node({'status': status})
                self.scene_util.status_updated(status=SceneTerminal.Status.HATCHING,
                                               scene_terminal_id=scene_terminal.pk,
                                               scene_terminal=scene_terminal)
            try:
                server = cloud.vm.check_create(server, **create_params)
            except Exception as e:
                try:
                    cloud.vm.delete(server.id)
                except Exception:
                    pass
                raise e
        elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
            with create_docker_lock(scene_terminal):
                create_params = cloud.docker.load_create_params(**create_params)
                server = cloud.docker.send_create(**create_params)
                status = self.get_latest_status(SceneTerminal.Status.HATCHING)
                if status == SceneTerminal.Status.HATCHING:
                    self.update_node({'status': status})
                    self.scene_util.status_updated(status=SceneTerminal.Status.HATCHING,
                                                   scene_terminal_id=scene_terminal.pk,
                                                   scene_terminal=scene_terminal)
                try:
                    server = cloud.docker.check_create(server, **create_params)
                except Exception as e:
                    try:
                        cloud.docker.delete(server.uuid)
                    except Exception:
                        pass
                    raise e
        else:
            raise SceneException(
                'envterminal[%s] invalid image type[%s]' % (scene_terminal.name, scene_terminal.image_type))

        mac_info = {}
        for subnet_infos in server.addresses.values():
            for subnet_info in subnet_infos:
                mac_info[subnet_info['addr']] = subnet_info.get('OS-EXT-IPS-MAC:mac_addr')

        return {
            'server': server,
            'server_id': server.id,
            'host_name': getattr(server, 'host_name', None),
            'host_ip': getattr(server, 'host_ip_address', None),
            'mac_info': mac_info,
        }

    def _server_bind_float_ip(self, server_id, float_ip_params):
        scene_terminal = self.node

        fixed_ip = float_ip_params['fixed_ip']
        network_id = float_ip_params['network_id']
        float_ip_info = float_ip_params['float_ip_info']
        if scene_terminal.image_type == SceneTerminal.ImageType.VM:
            fip_port = cloud.network.get_port(network_id, instance=cloud.vm.get(server_id))
            port_info = '_'.join([fip_port['id'], fixed_ip])
            cloud.vm.update(server_id, fip_port=port_info, float_ip=float_ip_info[1])
        elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
            fip_port = cloud.network.get_port(network_id, container=cloud.docker.get(server_id))
            port_info = '_'.join([fip_port['id'], fixed_ip])
            cloud.docker.update(server_id, fip_port=port_info, float_ip=float_ip_info[1])

    def _server_add_remote_connection(self, access_modes):
        scene_terminal = self.node

        is_add = False
        host_proxy_port_mapping = json.loads(scene_terminal.host_proxy_port)
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            if protocol not in remote_protocols:
                continue

            username = access_mode.get('username')
            if not username:
                continue

            connections = access_mode.get('connections', {})
            connection = connections.get(self.user.id, {})
            if connection.get('connection_id'):
                continue

            ip, port = get_ip_port_for_remote(scene_terminal, access_mode, host_proxy_port_mapping)
            if not ip:
                continue

            password = access_mode.get('password')
            if protocol == SceneTerminal.AccessMode.SSH:
                connection_id = self.add_ssh_connection(ip, port, username, password)
            else:
                rdp_params = {
                    'hostname': ip,
                    'port': port,
                    'username': username,
                    'password': password,
                    'system_type': scene_terminal.system_type,
                }
                security = access_mode.get('mode')
                if security:
                    rdp_params['security'] = security
                connection_id = self.add_rdp_connection(**rdp_params)

            connection['connection_id'] = connection_id
            connections[self.user.id] = connection
            access_mode['connections'] = connections
            is_add = True
        return is_add

    # 宿主机代理
    def create_host_proxy(self, server=None):
        scene_terminal = self.node
        scene_terminal_host_proxy_port = {}
        if scene_terminal.float_ip:
            return scene_terminal_host_proxy_port

        if not scene_terminal.host_ip:
            return scene_terminal_host_proxy_port

        if not server:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                server = cloud.vm.get(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                server = cloud.docker.get(scene_terminal.server_id)
            else:
                return scene_terminal_host_proxy_port

        access_modes = json.loads(scene_terminal.access_modes) if scene_terminal.access_modes else []
        proxy_access_base_protocols = []
        proxy_access_protocols = []
        proxy_access_ports = []
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol, None))
            if port and access_mode.get('proxy'):
                proxy_access_base_protocols.append(
                    access_mode.get('base_protocol', SceneTerminal.AccessBaseProtocol.TCP))
                proxy_access_protocols.append(protocol)
                proxy_access_ports.append(port)

        if proxy_access_ports:
            network_id = get_terminal_network_id(scene_terminal)
            if not network_id:
                return

            for i, port in enumerate(proxy_access_ports):
                protocol = proxy_access_protocols[i]
                base_protocol = proxy_access_base_protocols[i]
                create_params = {
                    'protocol': base_protocol,
                    'port': port,
                    'network_id': network_id,
                }
                if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                    create_params['instance'] = server
                elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                    create_params['container'] = server
                try:
                    ret = cloud.network.create_portmapping(**create_params)
                except Exception as e:
                    logger.error('terminal[%s, host=%s] create host proxy error: %s', scene_terminal.name,
                                 scene_terminal.host_ip, e)
                    for proxy_info in scene_terminal_host_proxy_port.values():
                        try:
                            cloud.network.delete_portmapping(proxy_info['id'])
                        except Exception as se:
                            logger.error('terminal[%s, host=%s] rollback host proxy error: %s', scene_terminal.name,
                                         scene_terminal.host_ip, se)
                    raise e

                scene_terminal_host_proxy_port['%s:%s' % (protocol, port)] = {
                    'id': ret['id'],
                    'port': ret['port'],
                }
        return scene_terminal_host_proxy_port

    # 平台代理
    def create_proxy(self):
        scene_terminal = self.node

        access_modes = json.loads(scene_terminal.access_modes) if scene_terminal.access_modes else []
        proxy_access_protocols = []
        proxy_access_ports = []
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol, None))
            if port:
                proxy_access_protocols.append(protocol)
                proxy_access_ports.append(port)

        scene_terminal_proxy_port = {}
        if proxy_access_ports:
            proxy_ports = proxy.create_proxy(scene_terminal.float_ip, proxy_access_ports)
            for i, proxy_port in enumerate(proxy_ports):
                protocol = proxy_access_protocols[i]
                port = proxy_access_ports[i]
                scene_terminal_proxy_port['%s:%s' % (protocol, port)] = proxy_port
        return scene_terminal_proxy_port

    def create_qos(self, resource_name=None):
        scene_terminal = self.node

        policies = []
        create_func = (cloud.vm.create_qos
                       if scene_terminal.image_type == SceneTerminal.ImageType.VM
                       else cloud.docker.create_qos)
        net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
        for net_config in net_configs:
            net_sub_id = net_config['id']
            rule = {}
            if net_config.get('egress'):
                rule['egress'] = net_config.get('egress')
            if net_config.get('ingress'):
                rule['ingress'] = net_config.get('ingress')
            if rule:
                net = scene_terminal.nets.filter(sub_id=net_sub_id).first()
                if net:
                    name = '%s_%s' % ((resource_name or scene_terminal.name), net_sub_id)
                    net_id = cloud.get_external_net() if common.is_external_net(net_sub_id) else net.net_id
                    policy = create_func(name, scene_terminal.server_id, net_id, rule)
                    policies.append(policy['id'])

        return policies

    def local_create_server(self):
        scene_terminal = self.node

        proxy_port_info = json.loads(scene_terminal.proxy_port)
        if proxy_port_info:
            port_info = {}
            for key, p_port in proxy_port_info.items():
                port_info[key.split(':')[-1]] = p_port
            server = cloud.docker.local_create(port_info=port_info, image=scene_terminal.image)
        else:
            access_modes = json.loads(scene_terminal.access_modes) if scene_terminal.access_modes else []
            port_protocol = {}
            # 建连接
            for access_mode in access_modes:
                protocol = access_mode['protocol']
                port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol))
                if port:
                    port_protocol[port] = protocol
            server = cloud.docker.local_create(ports=port_protocol.keys(), image=scene_terminal.image)
            port_info = server.port_info
            proxy_port_info = {}
            for port, proxy_port in port_info.items():
                protocol = port_protocol[port]
                proxy_port_info['%s:%s' % (protocol, port)] = proxy_port

        return {
            'server_id': server.id,
            'proxy_port': proxy_port_info,
        }


class DeleteMixin(object):

    def delete_resource(self, shutdown=False, restart_proxy=False):
        self.delete_host_proxy_resource()
        self.detach_volumes()
        self.delete_server_resource(shutdown)
        self.delete_qos_resource()
        self.delete_net_port_resource()
        self.delete_float_ip_resource()
        self.delete_remote_resource()
        has_proxy = self.delete_proxy_resource(force_restart=restart_proxy)

        return {
            'has_proxy': has_proxy
        }

    def detach_volumes(self):
        scene_terminal = self.node

        volumes = json.loads(scene_terminal.volumes)
        for volume_id in volumes:
            try:
                common.detach_disk(scene_terminal.server_id, volume_id)
            except Exception:
                pass

    def delete_server_resource(self, shutdown=False):
        scene_terminal = self.node

        if scene_terminal.server_id:
            if scene_terminal.image_type == SceneTerminal.ImageType.VM:
                if shutdown:
                    cloud.vm.stop(scene_terminal.server_id)
                cloud.vm.delete(scene_terminal.server_id)
            elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                if shutdown:
                    cloud.docker.stop(scene_terminal.server_id, local=self.scene_util.is_local,
                                      host=scene_terminal.host_ip)
                cloud.docker.delete(scene_terminal.server_id, local=self.scene_util.is_local,
                                    host=scene_terminal.host_ip)

    def delete_net_port_resource(self):
        scene_terminal = self.node

        if scene_terminal.net_ports:
            net_ports = json.loads(scene_terminal.net_ports)
            for port_id in net_ports:
                try:
                    cloud.network.delete_port(port_id)
                except Exception:
                    pass

    def delete_float_ip_resource(self):
        scene_terminal = self.node

        if scene_terminal.float_ip_params:
            float_ip_params = json.loads(scene_terminal.float_ip_params)
            float_ip_info = float_ip_params.get('float_ip_info')
            if float_ip_info:
                try:
                    cloud.network.delete_fip(float_ip_info[1])
                except Exception:
                    pass

    def delete_remote_resource(self):
        scene_terminal = self.node

        if self.remote:
            access_modes = json.loads(scene_terminal.access_modes)
            for access_mode in access_modes:
                connections = access_mode.get('connections', {})
                for user_id, connection in connections.items():
                    connection_id = connection.get('connection_id')
                    if connection_id:
                        self.remove_connection(connection_id)

    def delete_host_proxy_resource(self):
        scene_terminal = self.node
        host_proxy_port = json.loads(scene_terminal.host_proxy_port)
        for proxy_info in host_proxy_port.values():
            try:
                cloud.network.delete_portmapping(proxy_info['id'])
            except Exception:
                pass

    def delete_proxy_resource(self, force_restart=False):
        scene_terminal = self.node

        has_proxy = False
        if self.proxy and (scene_terminal.float_ip or scene_terminal.host_ip):
            try:
                ports = [port_info.split(':')[1] for port_info in json.loads(scene_terminal.proxy_port).keys()]
            except Exception as e:
                logger.error('terminal[%s] delete proxy[%s] error: %s', scene_terminal.pk, scene_terminal.proxy_port, e)
            else:
                has_proxy = True
                proxy.delete_proxy(scene_terminal.float_ip or scene_terminal.host_ip, ports)

        if has_proxy and force_restart:
            proxy.restart_proxy()

        return has_proxy

    def delete_qos_resource(self):
        scene_terminal = self.node

        policies = json.loads(scene_terminal.policies)
        for policy_id in policies:
            try:
                cloud.qos.delete(policy_id)
            except Exception:
                pass


class TerminalUtil(GetMixin,
                   CreateMixin,
                   DeleteMixin,
                   ControlMixin,
                   UtilMixin,
                   PropertyMixin,
                   NodeUtil):

    def __init__(self, scene_terminal):
        scene_terminal = get_obj(scene_terminal, SceneTerminal)
        super(TerminalUtil, self).__init__(scene_terminal)


def get_access_mode_key(access_mode):
    protocol = access_mode.get('protocol')
    port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol)) or ''
    return '%s:%s:%s' % (protocol, port, access_mode.get('username'))


def get_terminal_hang_info(scene_terminal):
    scene_hang_info = json.loads(scene_terminal.scene.hang_info)
    if not scene_hang_info:
        return None

    hang_terminals = scene_hang_info.get('terminals')
    if not hang_terminals:
        return None

    terminal_hang_dict = {hang_terminal['sub_id']: hang_terminal for hang_terminal in hang_terminals}
    terminal_hang_info = terminal_hang_dict.get(scene_terminal.sub_id)

    return terminal_hang_info


def get_terminal_ip_type(scene_terminal, hang_info=None):
    # 连接到外网的机器
    if scene_terminal.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
        return ip_type.OUTER_FIXED

    # 通过外网路由过来的网络可以分浮动ip
    if scene_terminal.external:
        for scene_net in scene_terminal.nets.all():
            for scene_gateway in scene_net.scenegateway_set.all():
                if scene_gateway.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
                    return ip_type.FLOAT

    # 场景机器挂载的网络指定可以分浮动ip
    if hang_info and hang_info.get('allocate_float_ip'):
        return ip_type.FLOAT

    # 没有连接任何网络的机器默认连接到外网
    if not hang_info and scene_terminal.nets.count() == 0:
        return ip_type.OUTER_FIXED

    return ip_type.INNER_FIXED


def get_terminal_external_net(scene_terminal):
    external_net = scene_terminal.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).first()
    if not external_net:
        for scene_net in scene_terminal.nets.all():
            for scene_gateway in scene_net.scenegateway_set.all():
                if scene_gateway.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
                    return scene_net
    return external_net


def can_terminal_access_externel(scene_terminal):
    # 直连外网
    if scene_terminal.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
        return True

    # 连接通过外网路由过来的网络
    for scene_net in scene_terminal.nets.all():
        for scene_gateway in scene_net.scenegateway_set.all():
            if scene_gateway.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
                return True
    return False


def get_ip_port_for_remote(scene_terminal, access_mode, host_proxy_port_mapping):
    protocol = access_mode['protocol']
    port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol))
    ip = scene_terminal.float_ip
    if not ip:
        host_proxy_port = host_proxy_port_mapping.get('%s:%s' % (protocol, port))
        if host_proxy_port:
            ip = scene_terminal.host_ip
            port = host_proxy_port['port']

    return ip, port


def get_terminal_network_id(scene_terminal):
    scene_net = scene_terminal.nets.filter(is_real=False).first()
    if scene_net:
        if common.is_external_net(scene_net.sub_id):
            return cloud.get_external_net()
        else:
            return scene_net.net_id

    if scene_terminal.scene.scenenet_set.count() == 0:
        return cloud.get_external_net()

    return None


def can_access_terminal(scene_terminal, standard_device=None):
    if scene_terminal.float_ip:
        return True

    host_proxy_port = json.loads(scene_terminal.host_proxy_port)
    if host_proxy_port:
        return True

    return False


def get_terminal_access_info(scene_terminal, standard_device=None):
    protocol = ''
    ip = ''
    port = ''
    if scene_terminal.float_ip:
        ip = scene_terminal.float_ip
        if standard_device:
            protocol = standard_device.access_mode
            # 有对应标靶并且有访问端口的情况检查端口
            if standard_device.access_port:
                port = int(standard_device.access_port)
            # 尝试从标靶访问方式获取默认端口
            elif protocol:
                port = SceneTerminal.AccessModeDefaultPort.get(protocol) or ''

        if not port:
            # 找不到标靶端口则从虚拟机配置端口找
            access_modes = json.loads(scene_terminal.access_modes)
            for access_mode in access_modes:
                protocol = access_mode['protocol']
                port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol)) or ''
                if port:
                    break
    else:
        host_proxy_port = json.loads(scene_terminal.host_proxy_port)
        if host_proxy_port:
            ip = scene_terminal.host_ip
            protocol = host_proxy_port.keys()[0].split(':')[0]
            port = host_proxy_port.values()[0]['port']

    return protocol, ip, port


def _access_info_key(protocol, ip, port):
    return '{}:{}:{}'.format(protocol, ip, port)


def get_terminal_access_infos(scene_terminal, standard_device=None):
    all_access_info = {}
    if scene_terminal.float_ip:
        ip = scene_terminal.float_ip

        if standard_device:
            protocol = standard_device.access_mode
            port = ''
            if standard_device.access_port:
                port = int(standard_device.access_port)
            elif protocol:
                port = SceneTerminal.AccessModeDefaultPort.get(protocol) or ''

            all_access_info[_access_info_key(protocol, ip, port)] = (protocol, ip, port)

        access_modes = json.loads(scene_terminal.access_modes)
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            port = access_mode.get('port', SceneTerminal.AccessModeDefaultPort.get(protocol)) or ''
            all_access_info[_access_info_key(protocol, ip, port)] = (protocol, ip, port)

    host_proxy_port = json.loads(scene_terminal.host_proxy_port)
    if host_proxy_port:
        ip = scene_terminal.host_ip

        for proxy_key, proxy_info in host_proxy_port.items():
            source_info = proxy_key.split(':')
            protocol = source_info[0]
            source_port = source_info[1]
            port = proxy_info['port']
            all_access_info[_access_info_key(protocol, ip, port)] = (protocol, ip, port, source_port)

    return all_access_info.values()
