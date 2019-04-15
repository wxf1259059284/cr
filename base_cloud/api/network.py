# -*- coding: utf-8 -*-
import random

from base_cloud.complex.views import BaseScene

from .utils import str_filter


class Network(object):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def create(self, name, cidr=None, gateway_ip=None, dns=None, dhcp=True):
        params = {
            'name': str_filter(name),
            'cidr': cidr,
            'gateway_ip': gateway_ip,
            'dns_nameservers': dns or [],
            'enable_dhcp': dhcp,
        }
        if cidr and not gateway_ip:
            params['gateway_ip'] = cidr[:-4] + '254'

        network, subnet = self.operator.scene_create_network(**params)

        return network, subnet

    def delete(self, network_id):
        try:
            self.operator.delete_network(network_id)
        except Exception:
            pass

    def create_subnet(self, network_id, **kwargs):
        if kwargs.get("name"):
            kwargs['name'] = str_filter(kwargs.get("name"))
        subnet = self.operator.create_subnet(network_id, **kwargs)
        return subnet

    def update_subnet(self, subnet_id, **kwargs):
        if kwargs.get("name"):
            kwargs['name'] = str_filter(kwargs.get("name"))
        self.operator.update_subnet(subnet_id, **kwargs)

    def create_vlan(self, name, vlan_id=None, cidr=None, gateway_ip=None, interfaces=None):
        if vlan_id is None:
            vlan_id = random.choice(list(set(range(1, 4097)) - set([int(vlan.get('vlan_id'))
                                                                    for vlan in self.operator.list_switch_vlans()])))

        vlan_net, vlan_subnet, s_vlan = self.operator.scene_create_vlan_network(name, vlan_id=str(vlan_id),
                                                                                cidr=cidr, gateway=gateway_ip,
                                                                                interfaces=interfaces)
        return vlan_net, vlan_subnet, s_vlan, vlan_id

    def delete_vlan(self, network_id):
        self.operator.scene_delete_vlan_network(network_id)

    def get_avaliable_ips(self, network_id, cidr):
        prefix = cidr.replace('0/24', '')
        all_ips = ['%s%s' % (prefix, i) for i in range(2, 254)]
        ports = self.get_ports(network_id)
        used_ips = set()
        for port in ports:
            for fixed_ip in port.get('fixed_ips', []):
                ip_address = fixed_ip.get('ip_address')
                if ip_address:
                    used_ips.add(ip_address)
        ips = sorted(list(set(all_ips) - used_ips), key=lambda x: int(x.replace(prefix, '')))
        return ips

    def get_port(self, network_id=None, instance=None, container=None):
        return self.operator.scene_get_port(network_id, instance, container)

    def get_ports(self, network_id=None, device_id=None):
        return self.operator.get_ports(network_id, device_id)

    def preallocate_fips(self, count=None, pre_fips=None):
        if count:
            if count == 0:
                return {}

            fips = self.operator.preallocate_fips(count)
            if count > 0 and len(fips.keys()) < count:
                raise Exception('no enough floating ips')
            return fips
        elif pre_fips:
            fips = self.operator.preallocate_fips(pre_fips)
            if len(fips.keys()) < len(pre_fips):
                raise Exception('no enough floating ips')
            return fips
        else:
            return {}

    def preallocate_ports(self, network_id, count=None, pre_ips=None):
        if count:
            ports = self.operator.preallocate_ports(network_id, count)
        elif pre_ips:
            ports = self.operator.preallocate_ports(network_id, pre_ips)
        else:
            ports = []
        port_map = {}
        for port in ports:
            ip = port['fixed_ips'][0]['ip_address']
            port_map[ip] = port['id']

        return port_map

    def clean_used_fips(self, pre_fips):
        self.operator.clean_used_fips(pre_fips)

    def delete_fip(self, fip_id):
        self.operator.delete_fip(fip_id)

    def delete_port(self, port_id):
        self.operator.delete_port(port_id)

    def create_portmapping(self, protocol, port, network_id, instance=None, container=None):
        port_id = self.get_port(network_id, instance=instance, container=container)['id']
        portmapping = self.operator.neutron_cli.create_portmapping(port_id, protocol, port)['portmapping']
        return {
            'id': portmapping['id'],
            'port': portmapping['host_port'],
        }

    def delete_portmapping(self, id):
        return self.operator.neutron_cli.delete_portmapping(id)

    def list_portmappings(self):
        return self.operator.neutron_cli.list_portmappings()

    def show_portmapping(self, id, **_params):
        return self.operator.neutron_cli.show_portmapping(id)
