# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json

from django.conf import settings
from django.db.models import Q, F

from ..models import StandardDevice


# 获取对应标靶的信息
def get_device_info_mapping(images):
    from base_scene.cms.serializers import StandardDeviceSerializer

    devices = StandardDevice.objects.filter(
        Q(standarddevicesnapshot__name__in=images) | Q(name__in=images)
    ).annotate(snapshot_name=F('standarddevicesnapshot__name'))
    mapping = {}
    for device in devices:
        data = StandardDeviceSerializer(
            device,
            fields=('id', 'name', 'logo', 'init_support', 'gateway_port_configs', 'port_map', 'remote_address',
                    'snapshot')
        ).data

        gateway_port_configs = data['gateway_port_configs']
        if gateway_port_configs:
            try:
                data['gateway_port_configs'] = json.loads(gateway_port_configs)
            except Exception:
                data['gateway_port_configs'] = []
        else:
            data['gateway_port_configs'] = []

        port_map = data['port_map']
        if port_map:
            try:
                data['port_map'] = json.loads(port_map)
            except Exception:
                data['port_map'] = []
        else:
            data['port_map'] = []

        if device.snapshot_name:
            mapping[device.snapshot_name] = data
        else:
            mapping[device.name] = data
    return mapping


class VisConfigHandler(object):
    def __init__(self, config):
        self.scene = config['scene']
        self.nodes = config['nodes']
        self.edges = config['edges']
        self.id_node = {node['id']: node for node in self.nodes}
        network_nodes = filter(lambda node: node['data']['_category'] == 'network', self.nodes)
        network_node_ids = [node['id'] for node in network_nodes]
        self.network_edges = filter(lambda edge: edge['from'] in network_node_ids or edge['to'] in network_node_ids,
                                    self.edges)

    def _convert_network_node(self, node):
        data = node['data']
        network = {
            'id': data['id'],
            'name': data['name'],
            'image': data.get('image', ''),
            'range': data.get('range', ''),
            'gateway': data.get('gateway', ''),
            'dns': data.get('dns', []),
            'dhcp': data.get('dhcp', True),
            'isReal': data.get('isReal', False),
            'visible': data.get('visible', True),
        }
        return network

    def _convert_router_node(self, node):
        data = node['data']
        router = {
            'id': data['id'],
            'name': data['name'],
            'image': data.get('image', ''),
            'staticRouting': data.get('staticRouting', []),
            'canUserConfigure': data.get('canUserConfigure', False),
            'isReal': data.get('isReal', False),
            'visible': data.get('visible', True),
            'net': self._get_node_nets(node),
        }
        return router

    def _convert_firewall_node(self, node):
        data = node['data']
        router = {
            'id': data['id'],
            'name': data['name'],
            'image': data.get('image', ''),
            'staticRouting': data.get('staticRouting', []),
            'rule': data['rule'],
            'canUserConfigure': data.get('canUserConfigure', False),
            'isReal': data.get('isReal', False),
            'visible': data.get('visible', True),
            'net': self._get_node_nets(node),
        }
        return router

    def _convert_server_node(self, node):
        data = node['data']
        server = {
            'id': data['id'],
            'name': data['name'],
            'imageType': data['imageType'],
            'systemType': data['systemType'],
            'systemSubType': data.get('systemSubType') or StandardDevice.SystemSubType.OTHER,
            'image': data['image'],
            'role': data['role'],
            'isReal': data.get('isReal', False),
            'visible': data.get('visible', True),
            'net': self._get_node_nets(node),
            'external': data.get('external', False),
            'flavor': data.get('flavor', ''),
            'accessMode': data.get('accessMode', []),
            'installers': data.get('installers', []),
            'customScript': data.get('customScript', ''),
            'initScript': data.get('initScript', ''),
            'installScript': data.get('installScript', ''),
            'deployScript': data.get('deployScript', ''),
            'cleanScript': data.get('cleanScript', ''),
            'pushFlagScript': data.get('pushFlagScript', ''),
            'checkScript': data.get('checkScript', ''),
            'attackScript': data.get('attackScript', ''),
            'checker': data.get('checker', ''),
            'attacker': data.get('attacker', ''),
            'extra': data.get('extra', ''),
        }

        return server

    def _get_node_nets(self, node):
        nets = []
        net_configs = node['data'].get('netConfigs', [])
        net_config_dict = {net_config['id']: net_config for net_config in net_configs}

        for edge in self.network_edges:
            if edge['from'] == node['id']:
                network_node_id = edge['to']
            elif edge['to'] == node['id']:
                network_node_id = edge['from']
            else:
                continue
            network_node = self.id_node.get(network_node_id)
            net_id = network_node['data']['id']
            if net_id in net_config_dict:
                nets.append(net_config_dict[net_id])
            else:
                nets.append(net_id)
        return nets

    def convert(self):
        json_config = {}
        json_config['scene'] = self.scene

        networks = []
        routers = []
        firewalls = []
        servers = []
        for node in self.nodes:
            category = node['data']['_category']
            if category == 'network':
                network = self._convert_network_node(node)
                if network:
                    networks.append(network)
            elif category == 'router':
                router = self._convert_router_node(node)
                routers.append(router)
            elif category == 'firewall':
                firewall = self._convert_firewall_node(node)
                firewalls.append(firewall)
            elif category == 'server':
                server = self._convert_server_node(node)
                servers.append(server)
        if networks:
            json_config['networks'] = networks
        if routers:
            json_config['routers'] = routers
        if firewalls:
            json_config['firewalls'] = firewalls
        if servers:
            json_config['servers'] = servers
        return json_config


DEFAULT_NETWORK_IMG = os.path.join(settings.MEDIA_URL, 'scene/default_node_logo/cloud.png')
DEFAULT_ROUTER_IMG = os.path.join(settings.MEDIA_URL, 'scene/default_node_logo/router.png')
DEFAULT_FIREWALL_IMG = os.path.join(settings.MEDIA_URL, 'scene/default_node_logo/firewall.png')
DEFAULT_SERVER_IMG = os.path.join(settings.MEDIA_URL, 'scene/default_node_logo/server.png')


class JsonConfigHandler(object):
    def __init__(self, config):
        # 后台返回完整的数据
        self.scene = config['scene']
        self.networks = config.get('networks', [])
        self.routers = config.get('routers', [])
        self.firewalls = config.get('firewalls', [])
        self.servers = config.get('servers', [])

        node_names = []
        node_names.extend([(network.get('image') or network['name']) for network in self.networks])
        node_names.extend([(router.get('image') or router['name']) for router in self.routers])
        node_names.extend([(firewall.get('image') or firewall['name']) for firewall in self.firewalls])
        node_names.extend([server['image'] for server in self.servers])

        self.device_info_mapping = get_device_info_mapping(node_names)

    def _convert_network(self, network):
        network_node = self._convert_common_info(network)
        name = network['name']
        image = network.get('image', '')

        device_info = self.device_info_mapping.get(image or name)
        img_url = device_info['logo'] if device_info else DEFAULT_NETWORK_IMG

        network_node.update({
            'image': img_url,
        })
        network_data = network_node['data']
        network_data.update({
            '_category': 'network',
            '_icon': img_url,
            'image': image,
            'range': network.get('range', ''),
            'gateway': network.get('gateway', ''),
            'dns': network.get('dns', []),
            'dhcp': network.get('dhcp', True),
            'isReal': network.get('isReal', False),
            'visible': network.get('visible', True),
        })

        return network_node

    def _convert_router(self, router):
        router_node = self._convert_common_info(router)
        name = router['name']
        image = router.get('image', '')

        device_info = self.device_info_mapping.get(image or name)
        img_url = device_info['logo'] if device_info else DEFAULT_ROUTER_IMG

        router_node.update({
            'image': img_url,
        })
        router_data = router_node['data']
        router_data.update({
            '_category': 'router',
            '_icon': img_url,
            '_deviceId': device_info['id'] if device_info else None,
            '_ports': device_info['port_map'] if device_info else [],
            'image': image,
            'staticRouting': router.get('staticRouting', []),
            'canUserConfigure': router.get('canUserConfigure', False),
            'isReal': router.get('isReal', False),
            'visible': router.get('visible', True),
        })
        self._update_net_info(router, router_node)

        return router_node

    def _convert_firewall(self, firewall):
        firewall_node = self._convert_common_info(firewall)
        name = firewall['name']
        image = firewall.get('image', '')

        device_info = self.device_info_mapping.get(image or name)
        img_url = device_info['logo'] if device_info else DEFAULT_FIREWALL_IMG

        firewall_node.update({
            'image': img_url,
        })
        firewall_data = firewall_node['data']
        firewall_data.update({
            '_category': 'firewall',
            '_icon': img_url,
            '_deviceId': device_info['id'] if device_info else None,
            '_ports': device_info['port_map'] if device_info else [],
            'image': image,
            'staticRouting': firewall.get('staticRouting', []),
            'rule': firewall['rule'],
            'canUserConfigure': firewall.get('canUserConfigure', False),
            'isReal': firewall.get('isReal', False),
            'visible': firewall.get('visible', True),
        })
        self._update_net_info(firewall, firewall_node)

        return firewall_node

    def _convert_server(self, server):
        server_node = self._convert_common_info(server)

        device_info = self.device_info_mapping.get(server['image'])
        if device_info:
            img_url = device_info['logo']
            images = [snapshot['name'] for snapshot in
                      sorted(device_info['snapshot'], key=lambda x: x['create_time'], reverse=True)]
            images.append(device_info['name'])
        else:
            img_url = DEFAULT_SERVER_IMG
            images = [server['image']]

        server_node.update({
            'image': img_url,
        })
        server_data = server_node['data']
        server_data.update({
            '_category': 'server',
            '_icon': img_url,
            '_images': images,
            '_deviceId': device_info['id'] if device_info else None,
            '_gateway_port_configs': device_info['gateway_port_configs'] if device_info else [],
            '_ports': device_info['port_map'] if device_info else [],
            '_remote_address': device_info['remote_address'] if device_info else None,
            'role': server['role'],
            'imageType': server['imageType'],
            'systemType': server['systemType'],
            'systemSubType': server.get('systemSubType') or StandardDevice.SystemSubType.OTHER,
            'image': server['image'],
            'initSupport': device_info['init_support'] if device_info else False,
            'isReal': server.get('isReal', False),
            'visible': server.get('visible', True),
            'external': server.get('external', False),
            'flavor': server.get('flavor', ''),
            'accessMode': server.get('accessMode', []),
            'installers': server.get('installers', []),
            'customScript': server.get('customScript', ''),
            'initScript': server.get('initScript', ''),
            'installScript': server.get('installScript', ''),
            'deployScript': server.get('deployScript', ''),
            'cleanScript': server.get('cleanScript', ''),
            'pushFlagScript': server.get('pushFlagScript', ''),
            'checkScript': server.get('checkScript', ''),
            'attackScript': server.get('attackScript', ''),
            'checker': server.get('checker', ''),
            'attacker': server.get('attacker', ''),
            'extra': server.get('extra', ''),
        })

        self._update_net_info(server, server_node)

        return server_node

    def _convert_common_info(self, source):
        node = {
            'data': {
                'id': source['id'],
                'name': source['name'],
            },
            'id': source['id'],
            'label': source['name'],
            'shape': 'circularImage',
            'readonly': False,
            'connections': set(),
            'raw_nets': source.get('net', [])
        }
        return node

    def _update_net_info(self, source, node):
        raw_nets = []
        net_configs = []
        for net in source.get('net', []):
            if isinstance(net, dict):
                net_configs.append(net)
                raw_nets.append(net['id'])
            else:
                raw_nets.append(net)
        node.update({'raw_nets': raw_nets})
        node['data'].update({'netConfigs': net_configs})

    def _generate_edges(self, node_id_map):
        edges = []
        # 已经添加过边的节点组
        connected_node_groups = []
        for node_id, node in node_id_map.items():
            connected_node_ids = node['connections']
            for connected_node_id in connected_node_ids:
                node_group = {node_id, connected_node_id}
                if node_group in connected_node_groups:
                    continue
                else:
                    connected_node_groups.append(node_group)
                edge = {
                    'from': node_id,
                    'to': connected_node_id,
                    "dashes": False
                }
                edges.append(edge)
        return edges

    def convert(self):
        # 转换节点信息
        network_nodes = []
        for network in self.networks:
            network_node = self._convert_network(network)
            network_nodes.append(network_node)

        router_nodes = []
        for router in self.routers:
            router_node = self._convert_router(router)
            router_nodes.append(router_node)

        firewall_nodes = []
        for firewall in self.firewalls:
            firewall_node = self._convert_firewall(firewall)
            firewall_nodes.append(firewall_node)

        server_nodes = []
        for server in self.servers:
            server_node = self._convert_server(server)
            server_nodes.append(server_node)

        nodes = []
        nodes.extend(network_nodes)
        nodes.extend(router_nodes)
        nodes.extend(firewall_nodes)
        nodes.extend(server_nodes)

        # 处理连接关系
        node_id_map = {}
        for node in nodes:
            node_id_map[node['id']] = node

        for node in nodes:
            node_id = node['id']
            connections = set()
            nets = node.pop('raw_nets')
            for net_id in nets:
                connected_node = node_id_map.get(net_id)
                if connected_node:
                    connections.add(connected_node['id'])
                    connected_node['connections'].add(node_id)
            node['connections'] = connections

        for node in nodes:
            node['connections'] = list(node['connections'])

        edges = self._generate_edges(node_id_map)

        data = {
            'scene': self.scene,
            'nodes': nodes,
            'edges': edges,
        }

        return data


def vis_to_backend(vis_config):
    handler = VisConfigHandler(vis_config)
    json_config = handler.convert()
    return json_config


def backend_to_vis(json_config):
    handler = JsonConfigHandler(json_config)
    vis_config = handler.convert()
    return vis_config
