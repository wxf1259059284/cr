# -*- coding: utf-8 -*-
import copy
import json
import jsonschema
import logging

from django.db import transaction
from django.utils import six, timezone
from django.utils.translation import ugettext_lazy as _

from base_scene.models import SceneConfig, StandardDevice, SceneTerminal
from base_scene.utils.common import is_external_net

from .error import error
from .exceptions import SceneException


logger = logging.getLogger(__name__)

IP_PATTERN_STR = (r'(?:(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:1[0-9][0-9]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.))'
                  r'{3}(?:(?:2[0-5][0-5])|(?:25[0-5])|(?:1[0-9][0-9])|(?:[1-9][0-9])|(?:[0-9]))')

IP_PATTERN = r'^' + IP_PATTERN_STR + r'$'

IP_PATTERN_E = r'^(' + IP_PATTERN_STR + r')?$'

CIDR_PATTERN = r'^' + IP_PATTERN_STR + r'/\d+$'

CIDR_PATTERN_E = r'^(' + IP_PATTERN_STR + r'/\d+)?$'

IP_OR_CIDR_PATTERN = r'^' + IP_PATTERN_STR + r'(/\d+)?$'

IP_OR_CIDR_PATTERN_E = r'^(' + IP_PATTERN_STR + r'(/\d+)?)?$'

PORT_OR_RANGE_STR = r'[1-9]\d{0,}(:[1-9]\d{0,})?'

PORT_OR_RANGE_PATTERN_E = r'^(' + PORT_OR_RANGE_STR + ')?$'


class JsonConfigParser(object):
    def __init__(self, content=None, file=None):
        if content:
            if isinstance(content, (six.string_types, six.text_type)):
                self.raw_config = json.loads(content)
            elif isinstance(content, dict):
                self.raw_config = content
            else:
                raise Exception('invalid content type: %s' % type(content))
        else:
            if not file:
                raise Exception('empty config')

            if isinstance(file, (six.string_types, six.text_type)):
                with open(file, 'r') as f:
                    self.raw_config = json.loads(f.read())
            elif hasattr(file, 'read'):
                self.raw_config = json.loads(file.read())
            else:
                raise Exception('invalid file type: %s' % type(content))

        if not self.raw_config:
            raise Exception('empty config')

        self.config = None

    def schema_validate(self):
        try:
            jsonschema.validate(self.raw_config, self.schema)
        except jsonschema.ValidationError as e:
            attr_name = e.schema.get('name') or e.schema.get('description')
            message = '{}[{}]: {}'.format(_('x_invalid_value'), attr_name, e.instance)
            raise SceneException(message)

    def extra_validate(self):
        self.config = self.raw_config

    def get_config(self):
        if self.config:
            return self.config
        self.schema_validate()
        self.extra_validate()
        return self.config


class SchemaPart(object):
    scene = {
        "description": "虚拟场景申明",
        "type": "object",
        "properties": {
            "name": {
                "description": "场景名称",
                "type": "string"
            },
            "desc": {
                "description": "场景描述",
                "type": "string"
            },
            "vulns": {
                "description": "关联漏洞",
                "$ref": "#/definitions/emptyStringArray"
            },
            "tools": {
                "description": "关联工具",
                "$ref": "#/definitions/emptyStringArray"
            },
            "tag": {
                "description": "标签",
                "$ref": "#/definitions/emptyStringArray"
            }
        },
        "required": ["name"]
    }
    network = {
        "type": "object",
        "properties": {
            "id": {
                "description": "网络id",
                "type": "string",
            },
            "name": {
                "description": "网络名称",
                "type": "string"
            },
            "image": {
                "name": "网络对应标靶",
                "description": "镜像名称或编号，需检查为系统中存在系统",
                "type": "string",
            },
            "range": {
                "name": "网段",
                "description": "未填写将自动分配，1.1.1.0/24",
                "type": "string",
                "pattern": CIDR_PATTERN_E,
            },
            "gateway": {
                "name": "网关",
                "description": "未填写将自动分配254",
                "type": "string",
                "pattern": IP_PATTERN_E,
            },
            "dns": {
                "name": "DNS",
                "description": "未填写将自动分配",
                "$ref": "#/definitions/emptyStringArray",
                "pattern": IP_PATTERN_E,
            },
            "dhcp": {
                "description": "dhcp",
                "type": "boolean",
            },
            "isReal": {
                "description": "是否是真实设备",
                "type": "boolean",
            },
            "visible": {
                "description": "是否显示",
                "type": "boolean",
            },
        },
        "required": ["id", "name"],
        "minItems": 0,
        "uniqueItems": True
    }

    net = {
        "anyOf": [
            {
                "type": "string"
            },
            {
                "type": "object",
                "properties": {
                    "id": {
                        "description": "网络id",
                        "type": "string",
                    },
                    "ip": {
                        "description": "ip",
                        "type": "string",
                        "pattern": IP_PATTERN_E,
                    },
                    "netmask": {
                        "description": "netmask",
                        "type": "string",
                        "pattern": IP_PATTERN_E,
                    },
                    "gateway": {
                        "description": "gateway",
                        "type": "string",
                        "pattern": IP_PATTERN_E,
                    },
                    "egress": {
                        "description": "egress",
                        "anyOf": [{
                            "type": "string",
                            "pattern": r"^$",
                        }, {
                            "type": "number",
                            "minimum": 0,
                        }]
                    },
                    "ingress": {
                        "description": "ingress",
                        "anyOf": [{
                            "type": "string",
                            "pattern": r"^$",
                        }, {
                            "type": "number",
                            "minimum": 0,
                        }]
                    },
                    "interfaces": {
                        "description": "连接端口",
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/positiveInteger"
                        },
                        "minItems": 0,
                        "uniqueItems": True
                    },
                    "gateway_port_id": {
                        "description": "虚拟网关端口id",
                        "type": "number",
                    },
                },
            }
        ]
    }

    static_routing = {
        "type": "object",
        "properties": {
            "destination": {
                "name": "静态路由目的地址",
                "description": "支持ip(1.1.1.1)或子网(1.1.1.0/24)",
                "type": "string",
                "pattern": IP_OR_CIDR_PATTERN,
            },
            "gateway": {
                "name": "静态路由下一跳地址",
                "description": "下一跳地址",
                "type": "string",
                "pattern": IP_PATTERN,
            }
        },
        "required": ["destination", "gateway"],
        "minItems": 0,
        "uniqueItems": True
    }

    router = {
        "type": "object",
        "properties": {
            "id": {
                "description": "路由id",
                "type": "string",
            },
            "name": {
                "description": "路由名称",
                "type": "string"
            },
            "image": {
                "name": "路由对应标靶",
                "description": "镜像名称或编号，需检查为系统中存在系统",
                "type": "string",
            },
            "net": {
                "description": "设备接入的网络",
                "type": "array",
                "items": net,
                "minItems": 0,
                "uniqueItems": True
            },
            "staticRouting": {
                "description": "静态路由表",
                "type": "array",
                "items": static_routing
            },
            "canUserConfigure": {
                "description": "是否支持用户侧配置",
                "type": "boolean",
            },
            "isReal": {
                "description": "是否是真实设备",
                "type": "boolean",
            },
            "visible": {
                "description": "是否显示",
                "type": "boolean",
            },
        },
    }

    firewall_rule = {
        "type": "object",
        "properties": {
            "protocol": {
                "name": "防火墙规则协议",
                "description": "必填，tcp/udp/icmp/any",
                "type": "string",
                "pattern": r"^tcp|udp|icmp|any$"
            },
            "action	": {
                "name": "防火墙规则行为",
                "description": "必填，allow/deny/reject",
                "type": "string",
                "pattern": r"^allow|deny|reject$"
            },
            "sourceIP": {
                "name": "防火墙规则源地址",
                "description": "选填，支持ip(1.1.1.1)或子网(1.1.1.0/24)，支持变量",
                "type": "string",
                "pattern": IP_OR_CIDR_PATTERN,
            },
            "destIP": {
                "name": "防火墙规则目的地址",
                "description": "选填，支持ip(1.1.1.1)或子网(1.1.1.0/24)，支持变量",
                "type": "string",
                "pattern": IP_OR_CIDR_PATTERN,
            },
            "sourcePort": {
                "name": "防火墙规则源端口",
                "description": "选填，支持单个prot或port range，支持变量",
                "type": "string",
                "pattern": PORT_OR_RANGE_PATTERN_E,
            },
            "destPort": {
                "name": "防火墙规则目的端口",
                "description": "选填，支持单个prot或port range，支持变量",
                "type": "string",
                "pattern": PORT_OR_RANGE_PATTERN_E,
            },
            "direction": {
                "name": "防火墙规则方向",
                "description": "选填，ingress/egress/both",
                "type": "string",
                "pattern": r"^$|ingress|egress|both$"
            },
        },
        "required": ["protocol", "action"],
    }
    firewall = {
        "type": "object",
        "properties": {
            "id": {
                "description": "防火墙id",
                "type": "string",
            },
            "name": {
                "description": "防火墙名称",
                "type": "string"
            },
            "image": {
                "name": "防火墙对应标靶",
                "description": "镜像名称或编号，需检查为系统中存在系统",
                "type": "string",
            },
            "net": {
                "description": "设备接入的网络",
                "type": "array",
                "items": net,
                "minItems": 0,
                "uniqueItems": True
            },
            "staticRouting": {
                "description": "静态路由表",
                "type": "array",
                "items": static_routing
            },
            "rule": {
                "description": "防火墙规则",
                "type": "array",
                "items": firewall_rule,
            },
            "canUserConfigure": {
                "description": "是否支持用户侧配置",
                "type": "boolean",
            },
            "isReal": {
                "description": "是否是真实设备",
                "type": "boolean",
            },
            "visible": {
                "description": "是否显示",
                "type": "boolean",
            },
        },
        "required": ["id", "name", "net"],
    }

    access_mode = {
        "type": "object",
        "properties": {
            "protocol": {
                "description": "协议",
                "type": "string",
            },
            "port": {
                "description": "端口",
                "oneOf": [{
                    "type": "string",
                    "pattern": r"^$",
                }, {
                    "type": "integer"
                }]
            },
            "mode": {
                "name": "rdp连接模式",
                "description": "连接模式, 暂时只有rdp有, rdp|nla",
                "type": "string",
                "pattern": r"^$|rdp|nla$"
            },
            "username": {
                "description": "用户",
                "type": "string",
            },
            "password": {
                "description": "密码",
                "type": "string",
            },
            "desc": {
                "description": "描述",
                "type": "string",
            },
            "proxy": {
                "description": "是否宿主机代理",
                "type": "boolean",
            },
            "base_protocol": {
                "description": "基础协议",
                "type": "boolean",
            },
        },
        "required": ["protocol"],
    }
    server = {
        "type": "object",
        "properties": {
            "id": {
                "description": "终端id",
                "type": "string",
            },
            "name": {
                "description": "终端名称",
                "type": "string"
            },
            "imageType": {
                "name": "镜像类型",
                "description": "镜像类型 支持 docker|vm",
                "type": "string",
                "pattern": r"^%s$" % '|'.join(SceneTerminal.ImageType.values()),
            },
            "systemType": {
                "name": "系统类型",
                "description": "系统类型 支持 linux|windows",
                "type": "string",
                "pattern": r"^%s$" % '|'.join(SceneTerminal.SystemType.values()),
            },
            "systemSubType": {
                "description": "系统详细类型",
                "type": "string",
                "pattern": r"^%s$" % '|'.join(SceneTerminal.SystemSubType.values()),
            },
            "image": {
                "name": "镜像名称",
                "description": "镜像名称或编号，需检查为系统中存在系统",
                "type": "string",
            },
            "flavor": {
                "description": "虚拟服务器大小",
                "type": "string",
                "pattern": r"^$|%s$" % '|'.join(StandardDevice.Flavor.values())
            },
            "role": {
                "name": "角色",
                "description": "operator/target/wingman/gateway 在场景中的角色,操作机和靶机会分配float_ip",
                "type": "string",
                "pattern": r"^operator|target|wingman|gateway|executer$"
            },
            "isReal": {
                "description": "是否是真实设备",
                "type": "boolean",
            },
            "visible": {
                "description": "是否显示",
                "type": "boolean",
            },
            "wanNumber": {
                "description": "wan口数量",
                "$ref": "#/definitions/positiveIntegerDefault0"
            },
            "lanNumber": {
                "description": "lan口数量",
                "$ref": "#/definitions/positiveIntegerDefault0"
            },
            "external": {
                "description": "外网是否需要直接访问",
                "type": "boolean",
            },
            "customScript": {
                "description": "自定义初始化脚本",
                "type": "string",
            },
            "initScript": {
                "description": "初始化脚本",
                "type": "string",
            },
            "installScript": {
                "description": "安装脚本",
                "type": "string",
            },
            "deployScript": {
                "description": "部署脚本",
                "type": "string",
            },
            "cleanScript": {
                "description": "清除脚本",
                "type": "string",
            },
            "pushFlagScript": {
                "description": "flag推送脚本",
                "type": "string",
            },
            "checkScript": {
                "description": "检查脚本",
                "type": "string",
            },
            "attackScript": {
                "description": "攻击脚本",
                "type": "string",
            },
            "checker": {
                "description": "检查脚本的执行者id",
                "type": "string",
            },
            "attacker": {
                "description": "攻击脚本的执行者id",
                "type": "string",
            },
            "accessMode": {
                "description": "常见可以用协议和端口",
                "type": "array",
                "items": access_mode,
                "minItems": 0,
                "uniqueItems": True
            },
            "installers": {
                "description": "安装工具列表",
                "$ref": "#/definitions/emptyStringArray"
            },
            "net": {
                "description": "设备接入的网络",
                "type": "array",
                "items": net,
                "minItems": 0,
                "uniqueItems": True
            },
            "extra": {
                "description": "自定义信息",
                "type": "string",
            },
        },
        "required": ["id", "name", "imageType", "image", "role"],
    }


# json schema验证配置
class JsonSceneConfigParser(JsonConfigParser):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "positiveInteger": {
                "minimum": 0,
                "type": "integer"
            },
            "positiveIntegerDefault0": {
                "allOf": [
                    {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    {
                        "default": 0
                    }
                ]
            },
            "schemaArray": {
                "items": {
                    "$ref": "#"
                },
                "minItems": 1,
                "type": "array"
            },
            "simpleTypes": {
                "enum": [
                    "array",
                    "boolean",
                    "integer",
                    "null",
                    "number",
                    "object",
                    "string"
                ]
            },
            "stringArray": {
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True
            },
            "emptyStringArray": {
                "items": {
                    "type": "string"
                },
                "type": "array",
                "uniqueItems": True
            }
        },
        "title": "场景拓扑",
        "description": "实现方式，先申请网络，每个虚拟机关联N个网络，网络之间需要互通，只需要申请一个路由器连接需要互通的路由器即可",
        "type": "object",
        "properties": {
            "scene": SchemaPart.scene,
            "networks": {
                "description": "虚拟网络申明",
                "type": "array",
                "items": SchemaPart.network,
            },
            "routers": {
                "description": "虚拟路由申明",
                "type": "array",
                "items": SchemaPart.router,
                "minItems": 0,
                "uniqueItems": True
            },
            "firewalls": {
                "description": "防火墙申明",
                "type": "array",
                "items": SchemaPart.firewall,
                "minItems": 0,
                "uniqueItems": True
            },
            "servers": {
                "description": "虚拟机申明",
                "type": "array",
                "items": SchemaPart.server,
                "minItems": 0,
                "uniqueItems": True
            },
        },
        "required": ["scene"]
    }


# 环境配置处理
class SceneConfigHandler(object):
    def __init__(self, user, scene_config=None):
        self.user = user
        self.scene_config = scene_config

    def create(self, config, **extra_params):
        config = self.check_config(config)

        with transaction.atomic():
            scene = config['scene']
            params = {
                'user': self.user,
                'json_config': json.dumps(config),
                'name': scene['name'],
                'modify_user': self.user,
            }
            params.update(extra_params)
            self.scene_config = SceneConfig.objects.create(**params)

        return self.scene_config

    def update(self, config, **extra_params):
        scene_config = self.scene_config

        if not scene_config:
            return

        config = self.check_config(config)

        with transaction.atomic():
            # 更新场景信息
            scene = config['scene']
            scene_config.name = scene['name']
            # update方法文件保存不了, 使用save
            scene_config.json_config = json.dumps(config)
            scene_config.modify_user = self.user
            scene_config.modify_time = timezone.now()
            for field_name, value in extra_params.items():
                setattr(scene_config, field_name, value)
            scene_config.save()
        return scene_config

    def add_server(self, server):
        scene_config = self.scene_config
        config = self.load_config(scene_config.json_config)
        config.setdefault('servers', []).append(server)
        self.update(config)

    def remove_server(self, server_id):
        scene_config = self.scene_config
        config = self.load_config(scene_config.json_config)
        servers = config.get('servers', [])
        server_mapping = {server['id']: server for server in servers}
        if server_id in server_mapping:
            servers.remove(server_mapping[server_id])
            self.update(config)

    @classmethod
    def load_config(cls, config):
        if isinstance(config, dict):
            config = json.dumps(config)

        try:
            parser = JsonSceneConfigParser(config)
            return parser.get_config()
        except Exception as e:
            raise SceneException(e.message)

    @classmethod
    def check_config(cls, config):
        config = cls.load_config(config)
        cls.check_structure(config)
        return config

    @classmethod
    def check_structure(cls, config):
        networks = config.get('networks', [])
        network_info = cls.check_networks(networks) if networks else {}

        routers = config.get('routers', [])
        firewalls = config.get('firewalls', [])
        gateways = routers + firewalls
        gateway_info = cls.check_gateways(gateways, network_info) if gateways else {}

        servers = config.get('servers', [])
        server_info = cls.check_servers(servers, network_info, gateway_info) if servers else {}
        return network_info, gateway_info, server_info

    @classmethod
    def check_networks(cls, networks):
        network_info = {}
        for network in networks:
            net_id = network['id']
            net_name = network['name']
            if net_id in network_info:
                raise SceneException(error.DUMPLICATE_NETWORK_ID(id=net_name))
            network_info[net_id] = {
                'network': network,
                'gateways': [],
                'servers': [],
            }

        return network_info

    @classmethod
    def check_gateways(cls, gateways, network_info):
        gateway_info = {}
        for gateway in gateways:
            gateway_id = gateway['id']
            gateway_name = gateway['name']
            if gateway_id in gateway_info:
                raise SceneException(error.DUMPLICATE_GATEWAY_ID(id=gateway_name))

            gateway_net_ids, invalid_nets = cls.parse_nets(gateway, network_info)
            if invalid_nets:
                raise SceneException(error.INVALID_GATEWAY_NETS(id=gateway_name, nets=str(invalid_nets)))

            gateway_relation = {
                'gateway': gateway,
                'networks': [],
                'nets': gateway_net_ids,
            }
            gateway_info[gateway_id] = gateway_relation
            for gateway_net_id in gateway_net_ids:
                network_relation = network_info[gateway_net_id]
                # 实体设备只能连接实体网络
                if cls.is_real_access_device(gateway):
                    network_relation['network']['isReal'] = True

                gateway_relation['networks'].append(network_relation['network'])
                network_relation['gateways'].append(gateway)

        return gateway_info

    @classmethod
    def check_servers(cls, servers, network_info, gateway_info):
        server_info = {}
        ids = [server['id'] for server in servers]
        for server in servers:
            server_id = server['id']
            server_name = server['name']
            if server_id in server_info:
                raise SceneException(error.DUMPLICATE_SERVER_ID(id=server_name))

            checker = server.get('checker')
            if checker and checker not in ids:
                raise SceneException(error.CHECKER_SERVER_NOT_EXIST.format(id=checker))
            attacker = server.get('attacker')
            if attacker and attacker not in ids:
                raise SceneException(error.ATTACKER_SERVER_NOT_EXIST.format(id=checker))

            server_net_ids, invalid_nets = cls.parse_nets(server, network_info)
            if invalid_nets:
                raise SceneException(error.INVALID_SERVER_NETS(id=server_name, nets=str(invalid_nets)))

            external = server.get('external', False)
            if external and not cls.has_external_net(server_net_ids, network_info, gateway_info):
                raise SceneException(error.SERVER_CANT_ACCESS_EXTERNAL_NET.format(id=server_name))

            server_relation = {
                'server': server,
                'networks': [],
                'nets': server_net_ids,
            }
            server_info[server_id] = server_relation
            for server_net_id in server_net_ids:
                network_relation = network_info[server_net_id]
                # 实体设备只能连接实体网络
                if cls.is_real_access_device(server):
                    network_relation['network']['isReal'] = True

                server_relation['networks'].append(network_relation['network'])
                network_relation['servers'].append(server_id)

        return server_info

    @classmethod
    def parse_nets(self, data, network_info):
        nets = copy.copy(data.get('net', []))
        net_ids = []
        for net in nets:
            if isinstance(net, dict):
                net_ids.append(net['id'])
            else:
                net_ids.append(net)

        invalid_nets = list(set(net_ids) - set(network_info.keys()))
        return net_ids, invalid_nets

    @classmethod
    def is_real_access_device(self, data):
        if not data.get('isReal'):
            return False

        for net in data.get('net', []):
            if isinstance(net, dict) and net.get('interfaces'):
                return True

        return False

    @classmethod
    def has_external_net(cls, server_nets, network_info, gateway_info):
        for server_net_id in server_nets:
            if is_external_net(server_net_id):
                return True

        for server_net_id in server_nets:
            gateways = network_info[server_net_id]['gateways']
            for gateway in gateways:
                for gateway_net_id in gateway_info[gateway['id']]['nets']:
                    if is_external_net(gateway_net_id):
                        return True
        return False
