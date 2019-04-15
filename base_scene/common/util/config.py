# -*- coding: utf-8 -*-
import json

from base.utils.models.common import get_obj

from base_scene.models import StandardDevice, SceneConfig, Scene, SceneNet, SceneGateway, SceneTerminal
from base_scene.utils import common


class ConfigUtil(object):

    def __init__(self, user, scene_config, hang_info=None, super_viewer=False):
        self.user = user
        self.scene_config = get_obj(scene_config, SceneConfig)
        self.json_config = json.loads(self.scene_config.json_config)
        self.hang_info = hang_info or {}
        self.super_viewer = super_viewer

    def create_scene_structure(self, **params):
        create_params = {
            'user': self.user,
            'type': self.scene_config.type,
            'file': self.scene_config.file,
            'json_config': self.scene_config.json_config,
            'hang_info': json.dumps(self.hang_info),
            'status': Scene.Status.CREATING,
        }
        create_params.update(**params)
        scene = Scene.objects.create(**create_params)
        net_info = self._create_scene_nets_structure(scene)
        self._create_scene_gateways_structure(scene, net_info)
        self._create_scene_terminals_structure(scene, net_info)

        return scene

    def _create_scene_nets_structure(self, scene):
        net_info = {}
        networks = self.json_config.get('networks', [])
        for network in networks:
            create_params = {
                'scene': scene,
                'sub_id': network['id'],
                'name': network['name'],
                'gateway': network.get('gateway') or '',
                'dns': json.dumps(network.get('dns', [])),
                'cidr': network.get('range') if not common.is_external_net(network['id']) else '',
                'is_real': network.get('isReal', False),
                'visible': network.get('visible', True),
            }
            scene_net = SceneNet.objects.create(**create_params)
            net_info[scene_net.sub_id] = scene_net
        return net_info

    def _create_scene_gateways_structure(self, scene, net_info):
        gateway_info = {}

        routers = self.json_config.get('routers', [])
        firewalls = self.json_config.get('firewalls', [])

        def _create_scene_gateway(gateway, gtype):
            net_configs, net_subids = self._parse_net_configs(gateway)
            create_params = {
                'scene': scene,
                'type': gtype,
                'sub_id': gateway['id'],
                'name': gateway['name'],
                'static_routing': json.dumps(gateway.get('staticRouting', [])),
                'can_user_configure': gateway.get('canUserConfigure', False),
                'is_real': gateway.get('isReal', False),
                'visible': gateway.get('visible', True),
                'net_configs': json.dumps(net_configs),
            }
            if gtype == SceneGateway.Type.FIREWALL:
                create_params.update({
                    'firewall_rule': json.dumps(firewall.get('rule', [])),
                })
            scene_gateway = SceneGateway.objects.create(**create_params)
            scene_gateway.nets.set([net_info[net] for net in net_subids])
            gateway_info[scene_gateway.sub_id] = scene_gateway

        for router in routers:
            _create_scene_gateway(router, SceneGateway.Type.ROUTER)
        for firewall in firewalls:
            _create_scene_gateway(firewall, SceneGateway.Type.FIREWALL)

        return gateway_info

    def _create_scene_terminals_structure(self, scene, net_info):
        server_info = {}

        servers = self.json_config.get('servers', [])
        for server in servers:
            net_configs, net_subids = self._parse_net_configs(server)

            system_type = server['systemType']
            system_sub_type = server.get('systemSubType', SceneTerminal.SystemSubType.OTHER)
            if system_sub_type != SceneTerminal.SystemSubType.OTHER:
                system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
            access_modes = server.get('accessMode', [])
            if self.super_viewer and server['imageType'] == SceneTerminal.ImageType.VM:
                has_console = False
                for access_mode in access_modes:
                    if access_mode.get('protocol') == SceneTerminal.AccessMode.CONSOLE:
                        has_console = True
                        break

                if not has_console:
                    access_modes.append({'protocol': SceneTerminal.AccessMode.CONSOLE})

            create_params = {
                'scene': scene,
                'sub_id': server['id'],
                'name': server['name'],
                'image_type': server['imageType'],
                'system_type': system_type,
                'system_sub_type': system_sub_type,
                'image': server['image'],
                'role': server['role'],
                'is_real': server.get('isReal', False),
                'visible': server.get('visible', True),
                'flavor': server.get('flavor'),
                'custom_script': server.get('customScript'),
                'init_script': server.get('initScript'),
                'install_script': server.get('installScript'),
                'deploy_script': server.get('deployScript'),
                'clean_script': server.get('cleanScript'),
                'push_flag_script': server.get('pushFlagScript'),
                'check_script': server.get('checkScript'),
                'attack_script': server.get('attackScript'),
                'checker': server.get('checker'),
                'attacker': server.get('attacker'),
                'raw_access_modes': json.dumps(access_modes),
                'access_modes': json.dumps(access_modes),
                'installers': json.dumps(server.get('installers', [])),
                'external': server.get('external', False),
                'net_configs': json.dumps(net_configs),
                'extra': server.get('extra', ''),
                'status': SceneTerminal.Status.RUNNING if server.get('isReal') else SceneTerminal.Status.PREPARING,
            }
            scene_terminal = SceneTerminal.objects.create(**create_params)
            scene_terminal.nets.set([net_info[net] for net in net_subids])

            server_info[scene_terminal.sub_id] = scene_terminal

        return server_info

    def _parse_net_configs(self, data):
        net_configs = []
        net_subids = []
        for net in data.get('net', []):
            if isinstance(net, dict):
                net_configs.append(net)
                net_subids.append(net['id'])
            else:
                net_subids.append(net)
        return net_configs, net_subids
