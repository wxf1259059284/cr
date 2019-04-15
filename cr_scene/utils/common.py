# -*- coding: utf-8 -*-
import json
import logging

from base.utils import udict
from base.utils.enum import Enum

from base_scene.models import SceneTerminal
from base_scene.utils.common import is_external_net

logger = logging.getLogger(__name__)

FixedRole = Enum(
    ADMIN=1,
    REFEREE=2,
)

role_terminal_fields = Enum(
    ACCESS=None,
    FORBID=('id', 'sub_id', 'name', 'status'),
    PUBLIC=('id', 'sub_id', 'name', 'status', 'float_ip', 'access_mode'),
    HIDDEN=(),
)

role_raw_terminal_fields = Enum(
    ACCESS=None,
    FORBID=('_category', '_icon', '_instance', 'id', 'name', 'visible', 'isReal'),
    PUBLIC=('_category', '_icon', '_instance', 'id', 'name', 'visible', 'isReal'),
    HIDDEN=(),
)


def get_users_by_cr_event_scenes(cr_event_scenes):
    users = set()
    for cr_event_scene in cr_event_scenes:
        try:
            role_users_info = json.loads(cr_event_scene.roles)
        except Exception:
            pass
        else:
            for role_users in role_users_info:
                users.update(role_users.get('users', []))

    return users


# 获取用户可访问终端列表
def get_user_role_info(user_id, cr_event_scene, fields=None):
    user_roles = set()
    user_servers = set()
    try:
        role_users_list = json.loads(cr_event_scene.roles)
        user_roles = [role_users['role'] for role_users in role_users_list if user_id in role_users.get('users', [])]
        if udict.need_field('servers', fields):
            role_servers_list = json.loads(cr_event_scene.cr_scene.roles)
            for role_servers in role_servers_list:
                role = role_servers.get('value')
                servers = role_servers.get('servers')
                if role in user_roles and servers:
                    user_servers.update(servers)
    except Exception as e:
        logger.error('get event role users error: %s', e)

    data = {
        'roles': user_roles,
        'servers': user_servers,
    }

    return udict.filter_data(data, fields)


# 获取用户场景可读取数据字段配置
def get_role_scene_fields_config(user_id, cr_event_scene, public=False):
    try:
        if cr_event_scene.cr_scene_instance:
            json_config = json.loads(cr_event_scene.cr_scene_instance.json_config)
        else:
            json_config = json.loads(cr_event_scene.cr_scene.scene_config.json_config)
        source_servers = [server['id'] for server in json_config.get('servers', [])]
    except Exception as e:
        logger.error('get event json_config error: %s', e)
        raise e

    user_servers = get_user_role_info(user_id, cr_event_scene, fields=('servers',))['servers']
    forbid_servers = set(source_servers) - user_servers
    if forbid_servers:
        if public:
            return {
                'terminal': {forbid_server: role_terminal_fields.PUBLIC for forbid_server in forbid_servers},
                'raw_terminal': {forbid_server: role_raw_terminal_fields.PUBLIC for forbid_server in forbid_servers},
            }
        else:
            return {
                'terminal': {forbid_server: role_terminal_fields.FORBID for forbid_server in forbid_servers},
                'raw_terminal': {forbid_server: role_raw_terminal_fields.FORBID for forbid_server in forbid_servers},
            }
    else:
        return None


# 过滤出公开节点，目前连接外网和分配浮动ip的(拓扑中必须存在外网)
def filter_public_nodes(scene_data, public_net_id=None):
    vis_structure = scene_data['vis_structure']
    nodes = vis_structure['nodes']
    edges = vis_structure['edges']

    node_mapping = {}
    for node in nodes:
        node_mapping[node['id']] = node
        if not public_net_id:
            if node['data']['_category'] == 'network' and is_external_net(node['data']['id']):
                public_net_id = node['id']

    filter_nodes = []
    filter_edges = []
    if public_net_id:
        public_net_node = node_mapping[public_net_id]
        filter_nodes.append(public_net_node)
        # 直连公共网络的终端节点
        connections = public_net_node['connections']
        for connection in connections:
            connected_node = node_mapping[connection]
            category = connected_node['data']['_category']
            if category == 'server':
                filter_nodes.append(connected_node)

        # 级联路由公共网络的内网节点
        route_public_net_node_ids = set()
        for node in nodes:
            category = connected_node['data']['_category']
            connections = node['connections']
            if category in ('router', 'firewall') and public_net_id in connections:
                for connection in connections:
                    connected_node = node_mapping[connection]
                    if connected_node['data']['_category'] == 'network' and not is_external_net(connection):
                        route_public_net_node_ids.add(connection)
        # 级联路由公共网络的内网节点拥有的终端节点
        for route_public_net_node_id in route_public_net_node_ids:
            node = node_mapping[route_public_net_node_id]
            connections = node['connections']
            for connection in connections:
                connected_node = node_mapping[connection]
                if connected_node['data']['_category'] == 'server' and connected_node['data']['external']:
                    filter_nodes.append(connected_node)

        filter_node_ids = [filter_node['id'] for filter_node in filter_nodes]
        for edge in edges:
            if edge['from'] in filter_node_ids:
                if edge['to'] in filter_node_ids:
                    filter_edges.append(edge)
                else:
                    if edge['to'] in route_public_net_node_ids:
                        edge['to'] = public_net_id
                        filter_edges.append(edge)
            else:
                if edge['to'] in filter_node_ids:
                    if edge['from'] in route_public_net_node_ids:
                        edge['from'] = public_net_id
                        filter_edges.append(edge)
                else:
                    pass

    filter_node_ids = [filter_node['id'] for filter_node in filter_nodes]
    for node in filter_nodes:
        node['connections'] = filter(lambda x: x in filter_node_ids, node['connections'])

    vis_structure['nodes'] = filter_nodes
    vis_structure['edges'] = filter_edges


def get_public_data_ids(scene_config, public_net_id=None):
    networks = scene_config.get('networks', [])
    routers = scene_config.get('routers', [])
    firewalls = scene_config.get('firewalls', [])
    gateways = routers + firewalls
    servers = scene_config.get('servers', [])

    if not public_net_id:
        for network in networks:
            if is_external_net(network['id']):
                public_net_id = network['id']

    public_data_ids = set()
    if public_net_id:
        public_data_ids.add(public_net_id)

        # 级联路由公共网络的内网节点
        route_public_net_gateway_ids = set()
        route_public_net_network_ids = set()
        for gateway in gateways:
            gateway_nets = gateway.get('net', [])
            for gateway_net in gateway_nets:
                if isinstance(gateway_net, dict):
                    gateway_net_id = gateway_net.get('id')
                else:
                    gateway_net_id = gateway_net
                if gateway_net_id == public_net_id:
                    route_public_net_gateway_ids.add(gateway['id'])
                elif not is_external_net(gateway_net_id):
                    route_public_net_network_ids.add(gateway_net_id)

        # 直连公共网络的终端节点
        for server in servers:
            server_nets = server.get('net', [])
            for server_net in server_nets:
                if isinstance(server_net, dict):
                    server_net_id = server_net.get('id')
                else:
                    server_net_id = server_net
                if server_net_id == public_net_id or (
                        server_net_id in route_public_net_network_ids and server.get('external')):
                    public_data_ids.add(server['id'])

    return public_data_ids


def handle_public_terminal_data(data):
    if 'access_mode' in data:
        access_mode_map = {}
        for access_key, access_mode in data['access_mode'].items():
            if access_mode.get('protocol') not in (
                    SceneTerminal.AccessMode.SSH,
                    SceneTerminal.AccessMode.RDP,
                    SceneTerminal.AccessMode.CONSOLE,
            ):
                udict.filter_data(access_mode, fields=('protocol', 'port'))
                access_mode_map[access_key] = access_mode

        data['access_mode'] = access_mode_map


def filter_scene_data_fields(scene_data, fields=None):
    scene_fields = fields.get('scene') if fields else None
    net_fields = fields.get('net') if fields else None
    gateway_fields = fields.get('gateway') if fields else None
    terminal_fields = fields.get('terminal') if fields else None
    raw_net_fields = fields.get('raw_net') if fields else None
    raw_gateway_fields = fields.get('raw_gateway') if fields else None
    raw_terminal_fields = fields.get('raw_terminal') if fields else None

    udict.filter_data(scene_data, fields=scene_fields)

    sub_id_node_mapping = {node['data']['id']: node for node in scene_data['vis_structure']['nodes']}

    def filter_data_fields(data_fields, raw=True):
        if data_fields:
            for sub_id, fields in data_fields.items():
                if sub_id in sub_id_node_mapping:
                    node = sub_id_node_mapping[sub_id]
                    if raw:
                        udict.filter_data(node['data'], fields=fields)
                    else:
                        instance = node['data']['_instance']
                        udict.filter_data(instance, fields=fields)
                        handle_public_terminal_data(instance)

    filter_data_fields(raw_net_fields)
    filter_data_fields(raw_gateway_fields)
    filter_data_fields(raw_terminal_fields)
    filter_data_fields(net_fields, False)
    filter_data_fields(gateway_fields, False)
    filter_data_fields(terminal_fields, False)


def can_role_get_scene(user_id, cr_event_scene):
    user_roles = get_user_role_info(user_id, cr_event_scene, fields=('roles',))['roles']
    return bool(user_roles)


def can_role_control_scene(user_id, cr_event_scene):
    user_roles = get_user_role_info(user_id, cr_event_scene, fields=('roles',))['roles']
    return FixedRole.ADMIN in user_roles


def can_role_get_terminal(user_id, cr_event_scene, terminal_sub_id):
    user_servers = get_user_role_info(user_id, cr_event_scene, fields=('servers',))['servers']
    return terminal_sub_id in user_servers


def can_role_control_terminal(user_id, cr_event_scene, terminal_sub_id):
    user_servers = get_user_role_info(user_id, cr_event_scene, fields=('servers',))['servers']
    return terminal_sub_id in user_servers
