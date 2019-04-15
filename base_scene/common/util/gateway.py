import json
import re

from django.db import transaction

from base.utils import udict
from base.utils.models.common import get_obj
from base.utils.ulist import valuefilter

from base_cloud import api as cloud
from base_scene import app_settings
from base_scene.common.error import error
from base_scene.common.exceptions import SceneException
from base_scene.common.scene_config import IP_PATTERN, IP_OR_CIDR_PATTERN, PORT_OR_RANGE_PATTERN_E
from base_scene.models import SceneGateway

from .node import NodeUtil


ip_re = re.compile(IP_PATTERN)

ip_or_cidr_re = re.compile(IP_OR_CIDR_PATTERN)

port_or_range_e_re = re.compile(PORT_OR_RANGE_PATTERN_E)


class PropertyMixin(object):

    node_model = SceneGateway


class GetMixin(object):

    def get_data(self, category, fields=None):
        scene_gateway = self.node

        data = {
            'id': scene_gateway.id,
            'sub_id': scene_gateway.sub_id,
            'static_routing': json.loads(scene_gateway.static_routing) if scene_gateway.static_routing else []
        }
        if category == 'firewall':
            data.update({
                'firewall_rule': json.loads(scene_gateway.firewall_rule) if scene_gateway.firewall_rule else [],
            })
        return udict.filter_data(data, fields)


class ControlMixin(object):

    def add_static_routing(self, static_route):
        scene_gateway = self.node

        if not scene_gateway.can_user_configure:
            raise SceneException(error.NO_PERMISSION)

        static_route = self.valid_static_routing(static_route)
        static_routing = json.loads(scene_gateway.static_routing) if scene_gateway.static_routing else []
        if static_route in static_routing:
            raise SceneException(error.EXIST_STATIC_ROUTE)
        if not scene_gateway.router_id:
            raise SceneException(error.ROUTER_NOT_PREPARED)

        with transaction.atomic():
            if not scene_gateway.is_real:
                cloud.router.add_static_route(scene_gateway.router_id, static_route)
            static_routing.append(static_route)
            scene_gateway.static_routing = json.dumps(static_routing)
            scene_gateway.save()
        return static_routing

    def remove_static_routing(self, static_route):
        scene_gateway = self.node

        if not scene_gateway.can_user_configure:
            raise SceneException(error.NO_PERMISSION)

        static_route = self.valid_static_routing(static_route)
        static_routing = json.loads(scene_gateway.static_routing) if scene_gateway.static_routing else []
        if static_route not in static_routing:
            raise SceneException(error.STATIC_ROUTE_NOT_EXIST)

        with transaction.atomic():
            if not scene_gateway.is_real:
                cloud.router.remove_static_route(scene_gateway.router_id, static_route)
            static_routing.remove(static_route)
            scene_gateway.static_routing = json.dumps(static_routing)
            scene_gateway.save()
        return static_routing

    @classmethod
    def valid_static_routing(cls, static_route):
        route = {
            'destination': static_route.get('destination', ''),
            'gateway': static_route.get('gateway', ''),
        }
        if not ip_or_cidr_re.match(route['destination']) or not ip_re.match(route['gateway']):
            raise SceneException(error.INVALID_STATIC_ROUTE)
        return route

    @classmethod
    def _get_firewall_rule(cls, firewall_rule, firewall_rules):
        for rule in firewall_rules:
            if cloud.firewall._is_same_rule(firewall_rule, rule):
                return rule
        return None

    def add_firewall_rule(self, firewall_rule):
        scene_gateway = self.node

        if not scene_gateway.can_user_configure:
            raise SceneException(error.NO_PERMISSION)

        firewall_rule = self.valid_firewall_rule(firewall_rule)
        current_firewall_rules = json.loads(scene_gateway.firewall_rule) if scene_gateway.firewall_rule else []
        if self._get_firewall_rule(firewall_rule, current_firewall_rules):
            raise SceneException(error.EXIST_FIREWALL_RULE)
        if not scene_gateway.firewall_id:
            raise SceneException(error.FIREWALL_NOT_PREPARED)

        with transaction.atomic():
            if not scene_gateway.is_real:
                ingress_rules, egress_rules = cloud.firewall.add_rule(scene_gateway.firewall_id, firewall_rule)
                for gress_rule in (ingress_rules + egress_rules):
                    firewall_rule.setdefault('ids', []).append(gress_rule['id'])

            current_firewall_rules.append(firewall_rule)
            scene_gateway.firewall_rule = json.dumps(current_firewall_rules)
            scene_gateway.save()
        return current_firewall_rules

    def remove_firewall_rule(self, firewall_rule):
        scene_gateway = self.node

        if not scene_gateway.can_user_configure:
            raise SceneException(error.NO_PERMISSION)

        firewall_rule = self.valid_firewall_rule(firewall_rule)
        current_firewall_rules = json.loads(scene_gateway.firewall_rule) if scene_gateway.firewall_rule else []
        current_firewall_rule = self._get_firewall_rule(firewall_rule, current_firewall_rules)
        if not current_firewall_rule:
            raise SceneException(error.INVALID_FIREWALL_RULE)

        with transaction.atomic():
            if not scene_gateway.is_real:
                rule_ids = current_firewall_rule.get('ids', [])
                if rule_ids:
                    cloud.firewall.remove_rules(scene_gateway.firewall_id, rule_ids)
            current_firewall_rules.remove(current_firewall_rule)
            scene_gateway.firewall_rule = json.dumps(current_firewall_rules)
            scene_gateway.save()
        return current_firewall_rules

    @classmethod
    def valid_firewall_rule(cls, firewall_rule):
        rule = {
            'protocol': valuefilter(firewall_rule.get('protocol', ''), ('tcp', 'udp', 'icmp', 'any')),
            'action': valuefilter(firewall_rule.get('action', ''), ('allow', 'deny', 'reject')),
            'direction': valuefilter(firewall_rule.get('direction', ''), ('ingress', 'egress', 'both', '')),

            'sourceIP': firewall_rule.get('sourceIP', ''),
            'sourcePort': firewall_rule.get('sourcePort', ''),
            'destIP': firewall_rule.get('destIP', ''),
            'destPort': firewall_rule.get('destPort', ''),
        }
        if not rule['protocol'] \
                or not rule['action'] \
                or not ip_or_cidr_re.match(rule['sourceIP']) \
                or not ip_or_cidr_re.match(rule['destIP']) \
                or not port_or_range_e_re.match(rule['sourcePort']) \
                or not port_or_range_e_re.match(rule['destPort']):
            raise SceneException(error.INVALID_FIREWALL_RULE)

        return rule


class CreateMixin(object):

    def create_router(self, resource_name=None):
        scene_gateway = self.node

        nets = scene_gateway.nets.all()
        subnet_ids = [net.subnet_id for net in nets if net.subnet_id]
        static_routing = json.loads(scene_gateway.static_routing) if scene_gateway.static_routing else []
        param = {
            'name': resource_name or scene_gateway.name,
            'static_routing': static_routing,
            'subnet_ids': subnet_ids,
        }
        if scene_gateway.nets.filter(sub_id__istartswith=app_settings.EXTERNAL_NET_ID_PREFIX).exists():
            param['external_net_id'] = cloud.get_external_net()
        router = cloud.router.create(**param)
        return {
            'router_id': router['id']
        }

    def create_firewall(self, resource_name=None):
        scene_gateway = self.node

        network_ids = [net.net_id for net in scene_gateway.nets.all() if net.net_id]
        rule = json.loads(scene_gateway.firewall_rule) if scene_gateway.firewall_rule else None
        name = resource_name or scene_gateway.name
        firewall, ingress_rules, egress_rules = cloud.firewall.create(name, rule=rule, network_ids=network_ids)
        if rule:
            all_gress_rules = ingress_rules + egress_rules
            for raw_rule in rule:
                for gress_rule in all_gress_rules:
                    if cloud.firewall.is_same_rule(raw_rule, gress_rule):
                        raw_rule.setdefault('ids', []).append(gress_rule['id'])
            scene_gateway.firewall_rule = json.dumps(rule)

        return {
            'firewall_id': firewall['id']
        }


class DeleteMixin(object):

    def delete_resource(self):
        scene_gateway = self.node

        if scene_gateway.router_id:
            cloud.router.delete(scene_gateway.router_id)
        if scene_gateway.firewall_id:
            cloud.firewall.delete(scene_gateway.firewall_id)


class GatewayUtil(GetMixin, ControlMixin, CreateMixin, DeleteMixin, PropertyMixin, NodeUtil):

    def __init__(self, scene_gateway):
        scene_gateway = get_obj(scene_gateway, SceneGateway)
        super(GatewayUtil, self).__init__(scene_gateway)
