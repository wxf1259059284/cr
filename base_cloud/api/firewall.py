# -*- coding: utf-8 -*-

from base_cloud.complex.views import BaseScene


class Firewall(object):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def get(self, firewall_id):
        self.operator.get_firewall(firewall_id)

    def create(self, name, rule=None, network_ids=None):
        ports = []
        if network_ids:
            for network_id in network_ids:
                router_ifs = self.operator.get_router_ifs(network_id)
                if router_ifs:
                    ports.extend(router_ifs)
        ports = list(set(ports))
        return self.operator.scene_create_firewall(name=name, rule=rule, ports=ports)

    def delete(self, firewall_id):
        try:
            self.operator.scene_delete_firewall(firewall_id)
        except Exception:
            pass

    def add_rule(self, firewall_id, rule):
        return self.operator.scene_add_firewall_rules(firewall_id, [rule])

    def remove_rules(self, firewall_id, rule_ids):
        self.operator.scene_delete_firewall_rules(firewall_id, rules=rule_ids)

    @classmethod
    def is_same_rule(cls, raw_rule, scene_rule):
        raw_converted_rule = {
            "protocol": raw_rule.get("protocol"),
            "action": raw_rule.get("action"),
            "source_ip_address": raw_rule.get("sourceIP") or None,
            "source_port": raw_rule.get("sourcePort") or None,
            "destination_ip_address": raw_rule.get("destIP") or None,
            "destination_port": raw_rule.get("destPort") or None
        }
        return cls._is_same_rule(raw_converted_rule, scene_rule)

    @classmethod
    def _is_same_rule(cls, rule1, rule2):
        for key, value in rule1.items():
            if rule2.get(key) != value:
                return False
        return True
