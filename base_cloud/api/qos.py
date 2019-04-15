# -*- coding: utf-8 -*-

from base_cloud.complex.views import BaseScene


class Qos(object):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def create(self, name, docker_id=None, vm_id=None, network_id=None, rule=None):
        return self.operator.scene_create_qos(name=name, container=docker_id,
                                              instance=vm_id, network_id=network_id, rule=rule)

    def delete(self, policy_id):
        try:
            self.operator.scene_delete_qos_policy(policy_id)
        except Exception:
            pass
