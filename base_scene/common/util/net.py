# -*- coding: utf-8 -*-
import json

from base.utils import udict
from base.utils.models.common import get_obj

from base_cloud import api as cloud
from base_scene.models import SceneNet, SceneTerminal
from base_scene.utils import common

from .node import NodeUtil


class PropertyMixin(object):

    node_model = SceneNet


class UtilMixin(object):

    def need_proxy_router(self, attach_terminals=None):
        scene_net = self.node

        if scene_net.is_real:
            return False

        if common.is_external_net(scene_net.sub_id):
            return False

        if scene_net.scenegateway_set.exists():
            return False

        if attach_terminals is None:
            attach_terminals = scene_net.sceneterminal_set.filter(is_real=False)

        for scene_terminal in attach_terminals:
            if scene_terminal.role == SceneTerminal.Role.GATEWAY:
                return False

        for scene_terminal in attach_terminals:
            access_modes = json.loads(scene_terminal.access_modes) if scene_terminal.access_modes else []
            for access_mode in access_modes:
                if access_mode.get('proxy'):
                    return True

        return False


class GetMixin(object):

    def get_data(self, fields=None):
        scene_net = self.node

        data = {
            'id': scene_net.id,
            'sub_id': scene_net.sub_id,
            'cidr': scene_net.cidr,
        }

        return udict.filter_data(data, fields)


class CreateMixin(object):

    def create_network(self, resource_name=None, cidr=None, interfaces=None):
        scene_net = self.node

        resource_name = resource_name or scene_net.name
        cidr = cidr or scene_net.cidr

        if scene_net.is_real:
            network, subnet, vlan, vlan_id = cloud.network.create_vlan(resource_name, cidr=cidr,
                                                                       gateway_ip=scene_net.gateway,
                                                                       interfaces=interfaces)
        else:
            dns = json.loads(scene_net.dns) if scene_net.dns else None
            network, subnet = cloud.network.create(resource_name, cidr=cidr, dns=dns, dhcp=scene_net.dhcp)
            vlan_id = None
            vlan = {}

        return {
            'net_id': network['id'],
            'subnet_id': subnet['id'],
            'cidr': cidr,
            'vlan_id': vlan_id,
            'vlan_info': vlan,
        }

    def create_proxy_router(self, resource_name=None):
        scene_net = self.node

        param = {
            'name': resource_name or scene_net.name,
            'subnet_ids': [scene_net.subnet_id],
        }
        router = cloud.router.create(**param)

        return {
            'router_id': router['id']
        }


class DeleteMixin(object):

    def delete_resource(self):
        scene_net = self.node

        if scene_net.proxy_router_id:
            cloud.router.delete(scene_net.proxy_router_id)

        if scene_net.net_id:
            if scene_net.is_real:
                cloud.network.delete_vlan(scene_net.net_id)
            else:
                cloud.network.delete(scene_net.net_id)


class NetUtil(GetMixin, CreateMixin, DeleteMixin, UtilMixin, PropertyMixin, NodeUtil):

    def __init__(self, scene_net):
        scene_net = get_obj(scene_net, SceneNet)
        super(NetUtil, self).__init__(scene_net)
