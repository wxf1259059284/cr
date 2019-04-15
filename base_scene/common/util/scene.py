# -*- coding: utf-8 -*-
import logging
import json
import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.reverse import reverse

from base.utils import udict
from base.utils.enum import Enum
from base.utils.functional import cached_property
from base.utils.models.common import get_obj
from base.utils.text import md5
from base.utils.thread import async_exe

from base_proxy import api as proxy
from base_proxy import app_settings as proxy_settings
from base_cloud import api as cloud
from base_scene import app_settings
from base_scene.common.error import error
from base_scene.common.exceptions import SceneException
from base_scene.utils import common
from base_scene.utils.vis_config import backend_to_vis
from base_scene.models import Scene, SceneNet, SceneGateway, SceneTerminal

from .net import NetUtil
from .gateway import GatewayUtil
from .terminal import (TerminalUtil, ip_type, process_status as terminal_process_status,
                       using_status as terminal_using_status)
from .constants import StatusUpdateEvent


logger = logging.getLogger(__name__)


create_message = Enum(
    CREATE_NETWORK='正在创建网络{name}',
    CREATE_ROUTER='正在创建路由{name}',
    CREATE_FIREWALL='正在创建防火墙{name}',
    STRUCTURE_CREATED='网络网关已创建完成',
    CREATE_TERMINAL='正在创建终端{name}',
    CREATE_QOS='终端{name}正在创建qos',
    BIND_FLOATING_IP='终端{name}正在绑定弹性ip',
    TERMINAL_INIT='终端{name}正在初始化',
    TERMINAL_CREATED='终端{name}创建完成',
    SCENE_CREATED='场景创建完成',
)

using_status = (
    Scene.Status.RUNNING,
    Scene.Status.PAUSE,
)

default_name_prefix = 'default'

node_classes = (
    NetUtil,
    GatewayUtil,
    TerminalUtil,
)


class PropertyMixin(object):

    @cached_property
    def node_util_class_map(self):
        class_map = {}
        for node_util_class in node_classes:
            class_map[node_util_class.node_model.__name__] = node_util_class
        return class_map

    @cached_property
    def hang_info(self):
        return json.loads(self.scene.hang_info)

    @cached_property
    def status_updated(self):
        if self.scene.status_updated:
            execute = self.scene.status_updated.execute
        else:
            execute = None

        def wrapper(*args, **kwargs):
            if execute:
                async_exe(execute, args=args, kwargs=kwargs)

        return wrapper

    # 是否平台本地创建资源 docker
    @cached_property
    def is_local(self):
        scene = self.scene
        if self.hang_info:
            return False
        elif scene.scenenet_set.exclude(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
            return False
        elif scene.sceneterminal_set.exclude(image_type=SceneTerminal.ImageType.DOCKER).exists():
            return False
        else:
            return True

    @cached_property
    def scene_nets(self):
        return list(self.scene.scenenet_set.all())

    @cached_property
    def scene_gateways(self):
        return list(self.scene.scenegateway_set.all())

    @cached_property
    def scene_terminals(self):
        if self.scene is None:
            return []
        return list(self.scene.sceneterminal_set.all())

    @cached_property
    def virtual_scene_nets(self):
        return [scene_net for scene_net in self.scene_nets if not scene_net.is_real]

    @cached_property
    def virtual_scene_gateways(self):
        return [scene_gateway for scene_gateway in self.scene_gateways if not scene_gateway.is_real]

    @cached_property
    def virtual_scene_terminals(self):
        return [scene_terminal for scene_terminal in self.scene_terminals if not scene_terminal.is_real]

    @cached_property
    def real_scene_nets(self):
        return [scene_net for scene_net in self.scene_nets if scene_net.is_real]

    @cached_property
    def real_scene_gateways(self):
        return [scene_gateway for scene_gateway in self.scene_gateways if scene_gateway.is_real]

    @cached_property
    def real_scene_terminals(self):
        return [scene_terminal for scene_terminal in self.scene_terminals if scene_terminal.is_real]

    @cached_property
    def net_terminals(self):
        net_terminals_mapping = {}
        for scene_terminal in self.scene_terminals:
            for scene_net in scene_terminal.nets.all():
                net_terminals_mapping.setdefault(scene_net.sub_id, []).append(scene_terminal)
        return net_terminals_mapping

    @cached_property
    def net_real_attachs(self):
        net_real_attachs_mapping = {}
        for scene_gateway in self.real_scene_gateways:
            for scene_net in scene_gateway.nets.all():
                net_real_attachs_mapping.setdefault(scene_net.sub_id, []).append(scene_gateway)
        for scene_terminal in self.real_scene_terminals:
            for scene_net in scene_terminal.nets.all():
                net_real_attachs_mapping.setdefault(scene_net.sub_id, []).append(scene_terminal)
        return net_real_attachs_mapping


class NodeMixin(object):

    @classmethod
    def node_key(cls, node):
        return md5('{}:{}'.format(id(node), node.id))

    def add_node_util(self, node_util):
        node_util._scene = self.scene
        node_util._scene_util = self
        if hasattr(self, 'user'):
            node_util(self.user, self.remote, self.proxy)

        key = self.node_key(node_util.node)
        self._nodes[key] = node_util
        return node_util

    def add_node(self, node):
        node_util = self.node_util_class_map[node.__class__.__name__](node)
        self.add_node_util(node_util)
        return node_util

    def get_node(self, node):
        key = self.node_key(node)
        node_util = self._nodes.get(key)
        if not node_util:
            node_util = self.add_node(node)
        return node_util

    def get_net_util(self, scene_net):
        return self.get_node(get_obj(scene_net, SceneNet))

    def get_gateway_util(self, scene_gateway):
        return self.get_node(get_obj(scene_gateway, SceneGateway))

    def get_terminal_util(self, scene_terminal):
        return self.get_node(get_obj(scene_terminal, SceneTerminal))


class GetMixin(object):

    def get(self, complete=False, fields=None):
        # fields:
        # {
        #     'scene': fields,
        #     'net': {
        #         sub_id: fields,
        #     },
        #     'gateway': {
        #         sub_id: fields,
        #     },
        #     'terminal': {
        #         sub_id: fields,
        #     },
        #     'raw_net': {
        #         sub_id: fields,
        #     },
        #     'raw_gateway': {
        #         sub_id: fields,
        #     },
        #     'raw_terminal': {
        #         sub_id: fields,
        #     },
        #
        # }
        scene = self.scene
        scene_fields = fields.get('scene') if fields else None

        data = self.get_data(fields=scene_fields)
        if complete:
            # 创建中的环境返回预估创建时间
            if scene.status == Scene.Status.CREATING:
                loaded_seconds, remain_seconds = self.get_process_seconds()
                data['loaded_seconds'] = loaded_seconds
                data['estimate_remain_seconds'] = remain_seconds
            elif scene.status in using_status:
                data['running_seconds'] = int((timezone.now() - scene.created_time).total_seconds())
            data['vis_structure'] = self.get_vis_structure(fields=fields)
        return data

    def get_vis_structure(self, fields=None):
        scene = self.scene
        net_fields = fields.get('net') if fields else None
        gateway_fields = fields.get('gateway') if fields else None
        terminal_fields = fields.get('terminal') if fields else None
        raw_net_fields = fields.get('raw_net') if fields else None
        raw_gateway_fields = fields.get('raw_gateway') if fields else None
        raw_terminal_fields = fields.get('raw_terminal') if fields else None

        sub_id_scenenet = {scene_net.sub_id: scene_net for scene_net in self.scene_nets}
        sub_id_scenegateway = {scene_gateway.sub_id: scene_gateway for scene_gateway in self.scene_gateways}
        sub_id_sceneterminal = {scene_terminal.sub_id: scene_terminal for scene_terminal in self.scene_terminals}

        json_config = json.loads(scene.json_config)
        vis_structure = backend_to_vis(json_config)
        vis_nodes = vis_structure['nodes']
        id_node = {}
        sub_id_node = {}
        gateway_nodes = []
        server_nodes = []
        for node in vis_nodes:
            id_node[node['id']] = node
            node_data = node['data']
            sub_id_node[node_data['id']] = node
            category = node_data['_category']
            if category == 'network':
                scene_net = sub_id_scenenet[node_data['id']]
                net_util = self.get_net_util(scene_net)
                fields = net_fields.get(scene_net.sub_id) if net_fields else None
                data = net_util.get_data(fields=fields)

                raw_fields = raw_net_fields.get(scene_net.sub_id) if raw_net_fields else None
                udict.filter_data(node_data, fields=raw_fields)
            elif category in ('router', 'firewall'):
                gateway_nodes.append(node)
                scene_gateway = sub_id_scenegateway[node_data['id']]
                gateway_util = self.get_gateway_util(scene_gateway)
                fields = gateway_fields.get(scene_gateway.sub_id) if gateway_fields else None
                data = gateway_util.get_data(category, fields=fields)

                raw_fields = raw_gateway_fields.get(scene_gateway.sub_id) if raw_gateway_fields else None
                udict.filter_data(node_data, fields=raw_fields)
            elif category == 'server':
                server_nodes.append(node)
                scene_terminal = sub_id_sceneterminal[node_data['id']]
                terminal_util = self.get_terminal_util(scene_terminal)
                fields = terminal_fields.get(scene_terminal.sub_id) if terminal_fields else None
                data = terminal_util.get_data(fields=fields)

                raw_fields = raw_terminal_fields.get(scene_terminal.sub_id) if raw_terminal_fields else None
                udict.filter_data(node_data, fields=raw_fields)

            node_data['_instance'] = data

        # 网关的nat信息，前端实现
        # gateway_node_ids = [gateway_node['id'] for gateway_node in gateway_nodes]
        # for server_node in server_nodes:
        #     nat_info = server_node['data']['_instance'].get('nat_info')
        #     if not nat_info or not nat_info.get('route_net'):
        #         continue
        #
        #     route_net_node = sub_id_node[nat_info['route_net']]
        #     for connected_node_id in route_net_node.get('connections', []):
        #         if connected_node_id in gateway_node_ids:
        #             gateway_node = sub_id_node[connected_node_id]
        #             gateway_node_data = gateway_node['data']
        #             fields = gateway_fields.get(gateway_node_data['id']) if gateway_fields else None
        #             if udict.need_field('nat_list', fields):
        #                 gateway_instance = gateway_node_data['_instance']
        #                 gateway_instance.setdefault('nat_list', []).append(nat_info)
        #             break

        return vis_structure

    def get_data(self, fields=None):
        scene = self.scene

        logs = json.loads(scene.log)
        if logs:
            log = logs[-1]
            log = log['message'].format(**log['params'] or {})
        else:
            log = ''
        data = {
            'id': scene.id,
            'name': scene.name,
            'status': scene.status,
            'error': scene.error,
            'log': log,
        }
        return udict.filter_data(data, fields)

    # 获取最新状态
    def get_latest_status(self):
        try:
            latest_status = Scene.objects.filter(pk=self.scene.pk).values('status')[0]['status']
        except Exception:
            latest_status = self.scene.status

        return latest_status

    def get_process_seconds(self):
        consume_time = get_scene_estimate_consume_time(self.scene.json_config)
        return common.get_part_seconds(self.scene.create_time, consume_time)

    def get_resource_name(self, name):
        name_prefix = self.scene.name_prefix or default_name_prefix
        return '.'.join([app_settings.BASE_GROUP_NAME, name_prefix, self.scene.name, name])

    def get_all_remote_info(self):
        remote_info = {}
        for scene_terminal in self.scene_terminals:
            terminal_util = self.get_terminal_util(scene_terminal)
            terminal_remote_info = terminal_util.get_all_remote_info()
            remote_info[scene_terminal.sub_id] = terminal_remote_info
        return remote_info


class CreateMixin(object):

    def ensure_create_resource(self):
        if not hasattr(self, '_resource'):
            self._resource = {
                'host_proxy_ids': [],
                'proxys': {},
                'nets': [],
                'routers': [],
                'fips': {},
                'external_net_ports': {},
                'vms': [],
                'dockers': {},
                'firewalls': [],
                'policies': [],
            }

    def prepare_create(self, float_ips=None, pre_fips=None):
        self.float_ips = float_ips
        self.pre_fips = pre_fips

    def create_resource(self, prepare=False):
        scene = self.scene
        for scene_terminal in self.virtual_scene_terminals:
            self.status_updated(status=SceneTerminal.Status.PREPARING, scene_terminal_id=scene_terminal.pk,
                                scene_terminal=scene_terminal)
        self.status_updated(status=Scene.Status.CREATING, scene_id=scene.pk, scene=scene)

        self.ensure_create_resource()
        if self.is_local:
            async_exe(self._local_create_resourcem, (prepare,))
        else:
            async_exe(self._create_resource, (prepare,))

    def create_related_resources(self):
        self.ensure_create_resource()

        for scene_gateway in self.virtual_scene_gateways:
            if scene_gateway.type == SceneGateway.Type.FIREWALL and not scene_gateway.firewall_id:
                self.log(create_message.CREATE_FIREWALL, {'name': scene_gateway.name})
                resource_name = self.get_resource_name(scene_gateway.name)
                gateway_util = self.get_gateway_util(scene_gateway)
                firewall = gateway_util.create_firewall(resource_name)
                self._resource['firewalls'].append(firewall['firewall_id'])
                scene_gateway.firewall_id = firewall['firewall_id']
                scene_gateway.save()

        for scene_terminal in self.virtual_scene_terminals:
            if not json.loads(scene_terminal.policies):
                resource_name = self.get_resource_name('%s_qos' % scene_terminal.name)
                terminal_util = self.get_terminal_util(scene_terminal)
                policies = terminal_util.create_qos(resource_name)
                if policies:
                    self._resource['policies'].extend(policies)
                    scene_terminal.policies = json.dumps(policies)
                    scene_terminal.save()

    def rollback_resource(self):
        proxys = self._resource.get('proxys')
        if proxys:
            for ip, ports in proxys.items():
                try:
                    proxy.delete_proxy(ip, ports)
                except Exception:
                    pass
            try:
                proxy.restart_proxy()
            except Exception:
                pass

        host_proxy_ids = self._resource.get('host_proxy_ids')
        if host_proxy_ids:
            for host_proxy_id in host_proxy_ids:
                try:
                    cloud.network.delete_portmapping(host_proxy_id)
                except Exception:
                    pass

        policies = self._resource.get('policies')
        if policies:
            for policy_id in policies:
                try:
                    cloud.qos.delete(policy_id)
                except Exception:
                    pass

        fips = self._resource.get('fips')
        if fips:
            for ip, fip_id in fips.items():
                try:
                    cloud.network.delete_fip(fip_id)
                except Exception:
                    pass

        external_net_ports = self._resource.get('external_net_ports')
        if external_net_ports:
            for ip, port_id in external_net_ports.items():
                try:
                    cloud.network.delete_port(port_id)
                except Exception:
                    pass

        vms = self._resource.get('vms')
        if vms:
            for vm_id in vms:
                try:
                    cloud.vm.delete(vm_id)
                except Exception:
                    pass

        dockers = self._resource.get('dockers')
        if dockers:
            for docker_id, host_ip in dockers.items():
                try:
                    cloud.docker.delete(docker_id, local=self.is_local, host=host_ip)
                except Exception:
                    pass

        firewalls = self._resource.get('firewalls')
        if firewalls:
            for firewall_id in firewalls:
                try:
                    cloud.firewall.delete(firewall_id)
                except Exception:
                    pass

        routers = self._resource.get('routers')
        if routers:
            for router_id in routers:
                try:
                    cloud.router.delete(router_id)
                except Exception:
                    pass

        nets = self._resource.get('nets')
        if nets:
            for net_id in nets:
                try:
                    cloud.network.delete(net_id)
                except Exception:
                    pass

    def create_resource_end(self):
        scene = self.scene
        if scene.status == Scene.Status.CREATING:
            try:
                # 创建qos 防火墙
                self.create_related_resources()

                # 全部机器都启动部署完了, 记录整个环境启动时间和消耗时间
                current_time = timezone.now()
                consume_time = current_time - scene.create_time
                self.update({
                    'created_time': current_time,
                    'consume_time': int(consume_time.total_seconds()),
                    'status': Scene.Status.RUNNING,
                })
                self.log(create_message.SCENE_CREATED)
            except Exception as e:
                self.create_resource_failed(e)
            else:
                logger.info('scene[%s] create ok', scene.pk)
                self.status_updated(status=Scene.Status.RUNNING, scene_id=scene.pk, scene=scene)
        elif scene.status in using_status:
            pass
        else:
            # 如果环境已删除，删除环境
            current_time = timezone.now()
            consume_time = current_time - scene.create_time
            self.update({
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            })
            async_exe(self.delete_resource)

    def create_resource_failed(self, error):
        scene = self.scene

        logger.error('create scene[%s] resource error: %s', scene.id, error)

        self.rollback_resource()

        has_deleted = self.get_latest_status() == Scene.Status.DELETED
        try:
            self.update({
                'error': str(error),
                'status': Scene.Status.DELETED if has_deleted else Scene.Status.ERROR,
            })
        except Exception as e:
            logger.error('scene[%s] update except: %s' % (scene.id, e))
        else:
            if has_deleted:
                async_exe(self.delete_resource)
            else:
                self.status_updated(status=Scene.Status.ERROR, scene_id=scene.pk, scene=scene)

    def _local_create_resource(self, prepare=False):
        scene = self.scene
        try:
            terminal_sub_id_net = {}
            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)
                terminal_util.fix_create_prefer()
                net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
                terminal_sub_id_net[scene_terminal.sub_id] = {net_config['id']: net_config['ip'] for net_config in
                                                              net_configs}

            # 解析脚本
            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)
                update_params = {
                    'init_script': terminal_util.parse_script(scene_terminal.init_script, terminal_sub_id_net),
                    'install_script': terminal_util.parse_script(scene_terminal.install_script, terminal_sub_id_net),
                    'deploy_script': terminal_util.parse_script(scene_terminal.deploy_script, terminal_sub_id_net),
                    'clean_script': terminal_util.parse_script(scene_terminal.clean_script, terminal_sub_id_net),
                    'push_flag_script': terminal_util.parse_script(scene_terminal.push_flag_script,
                                                                   terminal_sub_id_net),
                    'check_script': terminal_util.parse_script(scene_terminal.check_script, terminal_sub_id_net),
                    'attack_script': terminal_util.parse_script(scene_terminal.attack_script, terminal_sub_id_net),
                    'status': SceneTerminal.Status.PREPARED,
                }
                terminal_util.update_node(update_params)
                self.status_updated(status=SceneTerminal.Status.PREPARED, scene_terminal_id=scene_terminal.pk,
                                    scene_terminal=scene_terminal)

            if prepare:
                pass
            else:
                # 创建
                for scene_terminal in self.virtual_scene_terminals:
                    def tmp_task(scene_terminal):
                        try:
                            self.local_create_terminal_task(scene_terminal)
                        except Exception as e:
                            self.create_resource_failed(e)
                    async_exe(tmp_task, (scene_terminal,))
        except Exception as e:
            self.create_resource_failed(scene, e)

    def _create_resource(self, prepare=False):
        scene = self.scene
        try:
            # 创建网络
            fixed_cidrs = []
            random_cidr_count = 0

            for scene_net in self.scene_nets:
                if not common.is_external_net(scene_net.sub_id):
                    if scene_net.cidr:
                        fixed_cidrs.append(scene_net.cidr)
                    else:
                        random_cidr_count += 1
            ran_cidrs = common.random_cidrs(random_cidr_count, fixed_cidrs) if random_cidr_count else []

            for scene_net in self.scene_nets:
                if not common.is_external_net(scene_net.sub_id):
                    self.log(create_message.CREATE_NETWORK, {'name': scene_net.name})
                    resource_name = self.get_resource_name(scene_net.name)

                    interfaces = []
                    if scene_net.is_real:
                        real_attachs = self.net_real_attachs.get(scene_net.sub_id)
                        for real_attach in real_attachs:
                            try:
                                net_configs = json.loads(real_attach.net_configs)
                            except Exception:
                                net_configs = []
                            for net_config in net_configs:
                                interfaces.extend(net_config.get('interfaces', []))

                    net_util = self.get_net_util(scene_net)
                    if scene_net.cidr:
                        network = net_util.create_network(resource_name, interfaces=interfaces)
                    else:
                        network = net_util.create_network(resource_name, ran_cidrs.pop(0), interfaces=interfaces)
                    self._resource['nets'].append(network['net_id'])
                    scene_net.net_id = network['net_id']
                    scene_net.subnet_id = network['subnet_id']
                    scene_net.cidr = network['cidr']
                    scene_net.vlan_id = network['vlan_id']
                    scene_net.vlan_info = json.dumps(network['vlan_info'])

                    if not scene_net.is_real:
                        attach_terminals = self.net_terminals.get(scene_net.sub_id)
                        if attach_terminals and net_util.need_proxy_router(attach_terminals=attach_terminals):
                            router = net_util.create_proxy_router('%s_proxy_router' % resource_name)
                            self._resource['routers'].append(router['router_id'])
                            scene_net.proxy_router_id = router['router_id']

                    scene_net.save()
                    self.status_updated(scene_net_id=scene_net.pk, scene_net=scene_net)

            # 创建网关(路由器、防火墙)
            for scene_gateway in self.virtual_scene_gateways:
                if scene_gateway.type in (SceneGateway.Type.ROUTER, SceneGateway.Type.FIREWALL):
                    if scene_gateway.type == SceneGateway.Type.ROUTER:
                        self.log(create_message.CREATE_ROUTER, {'name': scene_gateway.name})
                    resource_name = self.get_resource_name(scene_gateway.name)

                    gateway_util = self.get_gateway_util(scene_gateway)
                    router = gateway_util.create_router(resource_name)
                    self._resource['routers'].append(router['router_id'])

                    scene_gateway.router_id = router['router_id']
                    scene_gateway.save()

            # 创建终端
            # 预分配浮动ip
            float_ip_count = 0
            outer_ip_count = 0
            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)(self.user, self.proxy, self.remote)
                terminal_util.fix_create_prefer()
                # 连到外网的机器能分浮动ip
                if terminal_util.ip_type == ip_type.FLOAT:
                    float_ip_count += 1
                elif terminal_util.ip_type == ip_type.OUTER_FIXED:
                    outer_ip_count += 1
            if float_ip_count > 0:
                if self.float_ips is not None:
                    if len(self.float_ips.keys()) < float_ip_count:
                        raise SceneException(error.NO_ENOUGH_FLOAT_IP)
                    float_ips = {}
                    for key in self.float_ips.keys()[:float_ip_count]:
                        float_ips[key] = self.float_ips.pop(key)
                elif self.pre_fips is not None:
                    if len(self.pre_fips) < float_ip_count:
                        raise SceneException(error.NO_ENOUGH_FLOAT_IP)
                    float_ips = cloud.network.preallocate_fips(pre_fips=self.pre_fips[:float_ip_count])
                else:
                    float_ips = cloud.network.preallocate_fips(float_ip_count)
            else:
                float_ips = {}
            self._resource['fips'] = float_ips
            float_ip_list = float_ips.items()

            # 预分配外网ip
            if outer_ip_count > 0:
                external_net_ports = cloud.network.preallocate_ports(cloud.get_external_net(), outer_ip_count)
            else:
                external_net_ports = {}
            self._resource['external_net_ports'] = external_net_ports
            external_net_port_list = external_net_ports.items()
            if len(external_net_port_list) < outer_ip_count:
                raise SceneException(error.NO_ENOUGH_EXTERNAL_NET_PORT)

            # 预分配固定ip
            declared_ips = {}
            random_ip_count = {}
            net_sub_id_cidr = {}
            for scene_terminal in self.virtual_scene_terminals:
                net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
                net_config_dict = {net_config['id']: net_config for net_config in net_configs}
                for net in scene_terminal.nets.all():
                    if not common.is_external_net(net.sub_id):
                        net_sub_id_cidr[net.sub_id] = net.cidr
                        has_ip = False
                        if net.sub_id in net_config_dict:
                            net_config = net_config_dict[net.sub_id]
                            if net_config.get('ip'):
                                declared_ips.setdefault(net.sub_id, []).append(net_config.get('ip'))
                                has_ip = True
                        if not has_ip:
                            ip_count = random_ip_count.get(net.sub_id, 0)
                            ip_count += 1
                            random_ip_count[net.sub_id] = ip_count
            ran_ips = {}
            for net_sub_id, count in random_ip_count.items():
                cidr = net_sub_id_cidr[net_sub_id]
                ran_ips[net_sub_id] = common.random_ips(cidr, count, declared_ips.get(net_sub_id))

            terminal_sub_id_net = {}
            terminal_sub_id_networks = {}
            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)

                prepare_network_param = {
                    'ran_ips': ran_ips,
                }
                if terminal_util.ip_type == ip_type.FLOAT:
                    prepare_network_param['float_ip_info'] = float_ip_list.pop(0)
                elif terminal_util.ip_type == ip_type.OUTER_FIXED:
                    prepare_network_param['external_port_info'] = external_net_port_list.pop(0)
                network_info = terminal_util.prepare_network(**prepare_network_param)

                scene_terminal.net_configs = json.dumps(network_info['net_configs'])
                scene_terminal.float_ip = network_info['float_ip']
                scene_terminal.float_ip_params = json.dumps(network_info['float_ip_params'])
                scene_terminal.net_ports = json.dumps(network_info['net_ports'])

                terminal_sub_id_networks[scene_terminal.sub_id] = network_info['networks']
                # 全部net_config已分配好
                terminal_sub_id_net[scene_terminal.sub_id] = {net_config['id']: net_config['ip'] for net_config in
                                                              network_info['net_configs']}

            restart_proxy = False
            gateway_terminals = []
            normal_terminals = []
            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)
                # 解析脚本
                scene_terminal.init_script = terminal_util.parse_script(scene_terminal.init_script, terminal_sub_id_net)
                scene_terminal.install_script = terminal_util.parse_script(scene_terminal.install_script,
                                                                           terminal_sub_id_net)
                scene_terminal.deploy_script = terminal_util.parse_script(scene_terminal.deploy_script,
                                                                          terminal_sub_id_net)
                scene_terminal.clean_script = terminal_util.parse_script(scene_terminal.clean_script,
                                                                         terminal_sub_id_net)
                scene_terminal.push_flag_script = terminal_util.parse_script(scene_terminal.push_flag_script,
                                                                             terminal_sub_id_net)
                scene_terminal.check_script = terminal_util.parse_script(scene_terminal.check_script,
                                                                         terminal_sub_id_net)
                scene_terminal.attack_script = terminal_util.parse_script(scene_terminal.attack_script,
                                                                          terminal_sub_id_net)

                install_info = terminal_util.prepare_install()
                scene_terminal.volumes = json.dumps(install_info['volumes'])

                # 完成创建参数
                create_params = terminal_util.prepare_create_params(
                    resource_name=self.get_resource_name(scene_terminal.name),
                    networks=terminal_sub_id_networks[scene_terminal.sub_id],
                    report_started='"scene={scene}&server={server}&status={status}" "{report_url}"'.format(
                        scene=scene.id,
                        server=scene_terminal.sub_id,
                        status=SceneTerminal.Status.DEPLOYING,
                        report_url=settings.SERVER + reverse('api:cms:base_scene:report_server_status')
                    ),
                    report_inited='"scene={scene}&server={server}&status={status}" "{report_url}"'.format(
                        scene=scene.id,
                        server=scene_terminal.sub_id,
                        status=SceneTerminal.Status.RUNNING,
                        report_url=settings.SERVER + reverse('api:cms:base_scene:report_server_status')
                    ),
                    attach_url=(settings.SERVER + scene.file.url) if scene.file else None
                )
                scene_terminal.create_params = json.dumps(create_params)

                # 提前创建代理
                if self.proxy and scene_terminal.float_ip:
                    scene_terminal_proxy_port = terminal_util.create_proxy()
                    if scene_terminal_proxy_port:
                        restart_proxy = True
                        source_ports = [key.split(':')[1] for key in scene_terminal_proxy_port.keys()]
                        self._resource['proxys'].setdefault(scene_terminal.float_ip, set()).update(source_ports)
                        scene_terminal.proxy_port = json.dumps(scene_terminal_proxy_port)

                scene_terminal.save()

                # 分配创建任务
                if scene_terminal.role == SceneTerminal.Role.GATEWAY:
                    gateway_terminals.append(scene_terminal)
                else:
                    normal_terminals.append(scene_terminal)

            if restart_proxy:
                proxy.restart_proxy()

            # 同步创建虚拟网关机器
            for scene_terminal in gateway_terminals:
                self.create_terminal_task(scene_terminal)

            # 更新网络网关
            for scene_net in self.virtual_scene_nets:
                if scene_net.gateway and scene_net.subnet_id:
                    cloud.network.update_subnet(scene_net.subnet_id, gateway_ip=scene_net.gateway)

            if prepare:
                for scene_terminal in normal_terminals:
                    terminal_util = self.get_terminal_util(scene_terminal)
                    terminal_util.update_node({'status': SceneTerminal.Status.PREPARED})
                    self.status_updated(status=SceneTerminal.Status.PREPARED, scene_terminal_id=scene_terminal.pk,
                                        scene_terminal=scene_terminal)
                self.log(create_message.STRUCTURE_CREATED)
            else:
                # 异步创建其他机器
                for scene_terminal in normal_terminals:
                    def tmp_task(scene_terminal):
                        try:
                            self.create_terminal_task(scene_terminal)
                        except Exception as e:
                            import traceback
                            msg = traceback.format_exc()
                            logger.error(msg)
                            self.create_resource_failed(e)
                    async_exe(tmp_task, (scene_terminal,))

        except Exception as e:
            self.create_resource_failed(e)

    def create_terminal_error(self, scene_terminal, error):
        terminal_util = self.get_terminal_util(scene_terminal)
        try:
            terminal_util.update_node({
                'error': str(error),
                'status': SceneTerminal.Status.ERROR,
            })
        except Exception as e:
            logger.error('scene_terminal[%s] update except: %s' % (scene_terminal.id, e))
        else:
            self.status_updated(status=SceneTerminal.Status.ERROR, scene_terminal_id=scene_terminal.pk,
                                scene_terminal=scene_terminal)

    def create_terminal_task(self, scene_terminal):
        self.log(create_message.CREATE_TERMINAL, {'name': scene_terminal.name})

        terminal_util = self.get_terminal_util(scene_terminal)
        terminal_util.update_node({'status': SceneTerminal.Status.CREATING, 'create_time': timezone.now()})
        self.status_updated(status=SceneTerminal.Status.CREATING, scene_terminal_id=scene_terminal.pk,
                            scene_terminal=scene_terminal)

        create_params = json.loads(scene_terminal.create_params)
        # 耗时方法
        try:
            server = terminal_util.create_server(create_params)
        except Exception as e:
            self.create_terminal_error(scene_terminal, e)
            raise e
        server_id = server['server_id']
        if scene_terminal.image_type == SceneTerminal.ImageType.VM:
            self._resource['vms'].append(server_id)
        elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
            self._resource['dockers'][server_id] = server['host_ip']

        # 更新mac地址
        net_configs = json.loads(scene_terminal.net_configs) if scene_terminal.net_configs else []
        net_config_dict = {net_config['ip']: net_config for net_config in net_configs}
        for ip, mac_addr in server['mac_info'].items():
            net_config = net_config_dict.get(ip)
            if net_config:
                net_config['mac_addr'] = mac_addr

        update_params = {
            'server_id': server_id,
            'host_name': server['host_name'],
            'host_ip': server['host_ip'],
            'net_configs': json.dumps(net_configs),
        }

        float_ip_params = json.loads(scene_terminal.float_ip_params)
        if float_ip_params:
            self.log(create_message.BIND_FLOATING_IP, {'name': scene_terminal.name})
            try:
                terminal_util._server_bind_float_ip(server_id, float_ip_params)
            except Exception as e:
                self.create_terminal_error(scene_terminal, e)
                raise e

        terminal_util.update_node(update_params, save=False)
        if not scene_terminal.float_ip:
            host_proxy_port = terminal_util.create_host_proxy(server=server['server'])
            for proxy_info in host_proxy_port.values():
                self._resource['host_proxy_ids'].append(proxy_info['id'])
            update_params['host_proxy_port'] = json.dumps(host_proxy_port)
            terminal_util.update_node(update_params, save=False)

        if self.remote:
            access_modes = json.loads(scene_terminal.access_modes) if scene_terminal.access_modes else []
            if access_modes and terminal_util._server_add_remote_connection(access_modes):
                update_params['access_modes'] = json.dumps(access_modes)

        terminal_util.update_node(update_params)

        if scene_terminal.image_type == SceneTerminal.ImageType.VM and terminal_util.can_access:
            terminal_status = SceneTerminal.Status.STARTING
        else:
            if scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
                time.sleep(2)
            terminal_status = SceneTerminal.Status.RUNNING

        # 上报状态
        async_exe(self.report_terminal_status, (scene_terminal, terminal_status))
        if terminal_status not in terminal_using_status:
            def created():
                self.report_terminal_status(scene_terminal, SceneTerminal.Status.RUNNING)
            terminal_util.check_status(created)

    def local_create_terminal_task(self, scene_terminal):
        self.log(create_message.CREATE_TERMINAL, {'name': scene_terminal.name})

        terminal_util = self.get_terminal_util(scene_terminal)
        terminal_util.update_node({'status': SceneTerminal.Status.CREATING, 'create_time': timezone.now()})
        self.status_updated(status=SceneTerminal.Status.CREATING, scene_terminal_id=scene_terminal.pk,
                            scene_terminal=scene_terminal)

        try:
            server = terminal_util.local_create_server()
        except Exception as e:
            self.create_terminal_error(scene_terminal, e)
            raise e
        server_id = server['server_id']
        if scene_terminal.image_type == SceneTerminal.ImageType.VM:
            self._resource['vms'].append(server_id)
        elif scene_terminal.image_type == SceneTerminal.ImageType.DOCKER:
            self._resource['docker'].append(server_id)

        terminal_util.update_node({
            'server_id': server_id,
            'host_ip': settings.SERVER_IP,
            'proxy_port': json.dumps(server['proxy_port']),
        })
        # 上报状态
        async_exe(self.report_terminal_status, (scene_terminal, SceneTerminal.Status.RUNNING))

    # 更新虚拟机状态
    def report_terminal_status(self, scene_terminal, status):
        terminal_util = self.get_terminal_util(scene_terminal)

        terminal_latest_status = terminal_util.get_latest_status()
        # 如果已删除
        if terminal_latest_status == SceneTerminal.Status.DELETED:
            if status in terminal_using_status:
                terminal_util.delete_resource(restart_proxy=True)
            return

        # 如果状态非最新无需更新
        if status in terminal_process_status and status <= terminal_latest_status:
            return

        terminal_update_params = {'status': status}

        # 是否已经最终更新过
        is_updated_finally = SceneTerminal.objects.filter(pk=scene_terminal.pk,
                                                          status__in=terminal_using_status).exists()

        is_updating_finally = not is_updated_finally and status in terminal_using_status
        # 机器已启动部署完成, 记录启动时间和消耗时间
        if is_updating_finally:
            current_time = timezone.now()
            consume_time = current_time - scene_terminal.create_time
            terminal_update_params.update({
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            })
            self.log(create_message.TERMINAL_CREATED, {'name': scene_terminal.name})

            volumes = json.loads(scene_terminal.volumes)
            if volumes:
                terminal_util.attach_disk(volumes)

        terminal_util.update_node(terminal_update_params)
        self.status_updated(status=status, scene_terminal_id=scene_terminal.pk, scene_terminal=scene_terminal)

        # 全部机器都启动部署完了
        if (not is_updated_finally
                and status in terminal_using_status
                and not terminal_util.scene.sceneterminal_set.exclude(status__in=terminal_using_status).exists()):
            self.create_resource_end()

    def create_prepared_terminal(self, scene_terminal):
        if scene_terminal.status != SceneTerminal.Status.PREPARED:
            return

        self.ensure_create_resource()

        def tmp_task():
            try:
                if self.is_local:
                    self.local_create_terminal_task(scene_terminal)
                else:
                    self.create_terminal_task(scene_terminal)
            except Exception as e:
                self.create_resource_failed(e)
        async_exe(tmp_task)

    def recreate_terminal(self, scene_terminal):
        self.ensure_create_resource()

        # 删机器
        terminal_util = self.get_terminal_util(scene_terminal)
        terminal_util.delete_server_resource()
        terminal_util.delete_qos_resource()
        # 删qos
        policies = json.loads(scene_terminal.policies)
        if policies:
            scene_terminal.policies = '[]'
            scene_terminal.save()

        self.update({'status': Scene.Status.CREATING})
        self.status_updated(status=Scene.Status.CREATING, scene_id=scene_terminal.scene.pk, scene=scene_terminal.scene)

        def tmp_task():
            try:
                if self.is_local:
                    self.local_create_terminal_task(scene_terminal)
                else:
                    self.create_terminal_task(scene_terminal)
            except Exception as e:
                self.create_resource_failed(e)
        async_exe(tmp_task)


class ControlMixin(object):

    def pause(self, sync=False):
        scene = self.scene

        if scene.status == Scene.Status.RUNNING:
            now_time = timezone.now()
            with transaction.atomic():
                scene.sceneterminal_set.all().update(
                    pause_time=now_time,
                    status=SceneTerminal.Status.PAUSE,
                )
                self.update({
                    'pause_time': now_time,
                    'status': Scene.Status.PAUSE,
                })

            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)
                if sync:
                    terminal_util.pause()
                else:
                    async_exe(terminal_util.pause)
                self.status_updated(status=SceneTerminal.Status.PAUSE, scene_terminal_id=scene_terminal.pk,
                                    scene_terminal=scene_terminal, event=StatusUpdateEvent.SCENE_PAUSE)
            self.status_updated(status=Scene.Status.PAUSE, scene_id=scene.pk, scene=scene,
                                event=StatusUpdateEvent.SCENE_PAUSE)

    def recover(self, sync=False):
        scene = self.scene

        if scene.status == Scene.Status.PAUSE:
            with transaction.atomic():
                scene.sceneterminal_set.all().update(
                    pause_time=None,
                    status=SceneTerminal.Status.RUNNING,
                )
                self.update({
                    'pause_time': None,
                    'status': Scene.Status.RUNNING,
                })

            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)
                if sync:
                    terminal_util.recover()
                else:
                    async_exe(terminal_util.recover)
                self.status_updated(status=SceneTerminal.Status.RUNNING, scene_terminal_id=scene_terminal.pk,
                                    scene_terminal=scene_terminal, event=StatusUpdateEvent.SCENE_RECOVER)
            self.status_updated(status=Scene.Status.RUNNING, scene_id=scene.pk, scene=scene,
                                event=StatusUpdateEvent.SCENE_RECOVER)

    def add_terminal(self):
        pass

    def remove_terminal(self, scene_terminal):
        terminal_util = self.get_terminal_util(scene_terminal)
        terminal_util.update_node({'status': SceneTerminal.Status.DELETED})

        def tmp_delete_resource():
            try:
                res = terminal_util.delete_resource()
                if res['has_proxy']:
                    # 删完重启代理
                    proxy.restart_proxy()
            except Exception as e:
                logger.error('scene_terminal[%s] delete resource error: %s', scene_terminal.id, e)
        async_exe(tmp_delete_resource)


class DeleteMixin(object):

    def delete(self, shutdown=False, sync=False):
        scene = self.scene

        with transaction.atomic():
            scene.sceneterminal_set.update(status=SceneTerminal.Status.DELETED)
            self.update({'status': Scene.Status.DELETED})

        for scene_terminal in self.scene_terminals:
            self.status_updated(status=SceneTerminal.Status.DELETED, scene_terminal_id=scene_terminal.pk,
                                scene_terminal=scene_terminal, event=StatusUpdateEvent.SCENE_DELETE)
        self.status_updated(status=Scene.Status.DELETED, scene_id=scene.pk, scene=scene,
                            event=StatusUpdateEvent.SCENE_DELETE)

        if sync:
            self.delete_resource(shutdown=shutdown)
        else:
            async_exe(self.delete_resource, (shutdown,))

    def delete_resource(self, shutdown=False):
        scene = self.scene

        try:
            has_proxy = False
            for scene_terminal in self.virtual_scene_terminals:
                terminal_util = self.get_terminal_util(scene_terminal)
                res = terminal_util.delete_resource(shutdown)
                if res['has_proxy']:
                    has_proxy = True

            if has_proxy:
                # 删完重启代理
                proxy.restart_proxy()

            for scene_gateway in self.virtual_scene_gateways:
                gateway_util = self.get_gateway_util(scene_gateway)
                gateway_util.delete_resource()

            for scene_net in self.virtual_scene_nets:
                net_util = self.get_net_util(scene_net)
                net_util.delete_resource()
        except Exception as e:
            logger.error('scene[%s] delete resource error: %s', scene.id, e)


class SceneUtil(GetMixin, CreateMixin, ControlMixin, DeleteMixin, NodeMixin, PropertyMixin):

    def __init__(self, scene):
        self.scene = get_obj(scene, Scene)
        self._nodes = {}

    def __call__(self, user=None, remote=True, proxy=False):
        self.user = user
        self.remote = remote
        self.proxy = proxy and proxy_settings.SWITCH
        for node in self._nodes:
            node(user, remote, proxy)

        return self

    def update(self, params):
        self.scene.__dict__.update(params)
        Scene.objects.filter(pk=self.scene.pk).update(**params)

    def log(self, message, params=None):
        log = Scene.objects.filter(pk=self.scene.pk).values('log')[0]['log']
        try:
            log = json.loads(log)
        except Exception:
            log = []
        log.append({'message': message, 'params': params})
        self.update({'log': json.dumps(log)})
        self.status_updated(scene_id=self.scene.pk, scene=self.scene)


# 获取预估的场景创建消耗时间
def get_scene_estimate_consume_time(json_config):
    similar_scene = Scene.objects.filter(
        consume_time__gt=0,
        json_config=json_config,
    ).order_by('-create_time').first()
    consume_time = similar_scene.consume_time if similar_scene else None
    return consume_time
