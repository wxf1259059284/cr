from __future__ import unicode_literals

import collections
import functools
import logging
import uuid

from keystoneauth1.identity import v3
from keystoneauth1 import session
from neutronclient.v2_0 import client

try:
    from base_cloud import app_settings
except Exception:
    pass


LOG = logging.getLogger(__name__)
CACHE_KEY = 'neutron_all_networks'


def unescape_port_kwargs(**kwargs):
    for key in kwargs:
        if '__' in key:
            kwargs[':'.join(key.split('__'))] = kwargs.pop(key)
    return kwargs


def complete_uuid(key_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if key_name in kwargs:
                kwargs.update({key_name: self._complete_uuid(kwargs.get(key_name))})
            elif args:
                arg_list = list(args)
                arg_list[0] = self._complete_uuid(arg_list[0])
                args = tuple(arg_list)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class Client(object):
    device_owner_map = {
        'compute:': 'compute',
        'neutron:LOADBALANCER': 'loadbalancer',
    }

    def __init__(self, **kwargs):
        auth = v3.Password(
                auth_url=kwargs.get("auth_url") or app_settings.OS_AUTH.get("auth_url"),
                username=kwargs.get("username") or app_settings.OS_AUTH.get("username"),
                password=kwargs.get("password") or app_settings.OS_AUTH.get("password"),
                project_name=kwargs.get("project_name") or app_settings.OS_AUTH.get("project_name"),
                user_domain_id=kwargs.get("user_domain_id") or app_settings.OS_AUTH.get("user_domain_id"),
                project_domain_id=kwargs.get("project_domain_id") or app_settings.OS_AUTH.get("project_domain_id")
        )
        sess = session.Session(auth=auth)
        self.neutron_client = client.Client(session=sess)

    def _get_tenant_id(self):
        project_id = app_settings.OS_AUTH.get("project_id")
        if project_id:
            return project_id

        return self.neutron_client.httpclient.session.auth.auth_ref.project_id

    def network_get_all(self, **params):
        if not params.get("shared"):
            params['shared'] = False
        return self.neutron_client.list_networks(**params).get('networks')

    def network_get_by_name(self, network_name):
        networks = self.network_get_all()
        for network in networks:
            if network.get("name") == network_name:
                return network
        return None

    def network_list_by_name(self, prefix):
        nets = []
        networks = self.network_get_all()
        for network in networks:
            if network.get("name").startswith(prefix):
                nets.append(network)
        return nets

    def network_get(self, network_id, expand_subnet=True, **params):
        return self.neutron_client.show_network(network_id, **params).get('network')

    def network_create(self, **kwargs):
        LOG.debug("network_create(): kwargs = %s" % kwargs)
        params = {
            'name': kwargs['name'],
            'admin_state_up': (kwargs['admin_state_up'] == 'True'),
            'shared': kwargs.get('shared', False)
        }
        if "router:external" in kwargs:
            params.update({
                'shared': True,
                'router:external': kwargs.get("router:external") or False,
                'provider:network_type': kwargs.get("provider:network_type"),
                'provider:physical_network': kwargs.get("provider:physical_network"),
                'provider:segmentation_id': kwargs.get("provider:segmentation_id")
            })
        # if 'tenant_id' not in kwargs:
        #     params['tenant_id'] = self._get_tenant_id()
        body = {'network': params}
        return self.neutron_client.create_network(body=body).get("network")

    def network_delete(self, network_id):
        self.neutron_client.delete_network(network_id)

    def network_update(self, network_id, **kwargs):
        body = {'network': {}}
        params = {'name': kwargs['net_name'],
                  'admin_state_up': (kwargs['admin_state'] == 'True'),
                  'shared': kwargs.get('shared', False)}
        body['network'].update(params)
        return self.neutron_client.update_network(network_id, body=body).get("network")

    def show_network_ip_availability(self, network_id):
        ip_availability = self.neutron_client.show_network_ip_availability(network_id)
        return ip_availability.get("network_ip_availability", {})

    def ext_networks_list(self):
        return self.network_get_all(**{'shared': True, 'provider:network_type': "flat"})

    def subnet_get_all(self, **params):
        return self.neutron_client.list_subnets(**params).get('subnets')

    def ad_sbunets_get(self, prefix):
        subnets = self.subnet_get_all(network_id=app_settings.COMPLEX_MISC.get("ad_net")[0])
        for subnet in subnets:
            if subnet['name'] == prefix+"subnet":
                return subnet
        return None

    def subnet_get(self, subnet_id):
        return self.neutron_client.show_subnet(subnet_id).get('subnet')

    def subnet_get_by_network_id(self, network_id):
        return self.subnet_get_all(network_id=network_id)

    def subnet_create(self, network_id, **kwargs):
        params = {'name': kwargs.get("name"),
                  'cidr': kwargs.get("cidr"),
                  'ip_version': 4,
                  'gateway_ip': kwargs.get("gateway_ip"),
                  'enable_dhcp': kwargs.get("enable_dhcp", True),
                  'allocation_pools': kwargs.get("allocation_pools") or []
                  }
        if kwargs.get("dns_nameservers"):
            params.update({"dns_nameservers": kwargs.get("dns_nameservers")})
        # if 'tenant_id' not in kwargs:
        #     params['tenant_id'] = self._get_tenant_id()
        body = {'subnet': {'network_id': network_id}}
        body['subnet'].update(params)
        return self.neutron_client.create_subnet(body=body).get("subnet")

    def subnet_update(self, subnet_id, **kwargs):
        body = {'subnet': kwargs}
        return self.neutron_client.update_subnet(subnet_id, body=body).get("subnet")

    def subnet_delete(self, subnet_id):
        self.neutron_client.delete_subnet(subnet_id)

    def router_get(self, router_id):
        return self.neutron_client.show_router(router_id).get('router')

    def router_get_all(self):
        return self.neutron_client.list_routers(retrieve_all=True).get('routers')

    def router_create(self, **kwargs):
        LOG.debug("router_create():, kwargs=%s" % kwargs)
        body = {'router': {}}
        params = {'name': kwargs['name']}
        if 'admin_state_up' in kwargs and kwargs['admin_state_up']:
            params['admin_state_up'] = kwargs['admin_state_up']
        if 'external_network' in kwargs and kwargs['external_network']:
            params['external_gateway_info'] = {'network_id': kwargs['external_network']}
        # if 'tenant_id' not in kwargs:
        #     params['tenant_id'] = self._get_tenant_id()
        body['router'].update(params)
        return self.neutron_client.create_router(body=body).get('router')

    def router_delete(self, router_id):
        self.neutron_client.delete_router(router_id)

    def router_update(self, router_id, **kwargs):
        body = {'router': {}}
        # params = {'admin_state_up': (kwargs['admin_state'] == 'True'),
        #           'name': kwargs['name']}
        body['router'].update(kwargs)
        return self.neutron_client.update_router(router_id, body=body).get('router')

    def router_get_by_name(self, router_name):
        routers = self.router_get_all()
        for route in routers:
            if route.get("name") == router_name:
                return route
        return None

    def router_list_by_name(self, prefix):
        rts = []
        routers = self.router_get_all()
        for route in routers:
            if route.get("name").startswith(prefix):
                rts.append(route)
        return rts

    def router_interface_add(self, router_id, subnet_id=None, port_id=None):
        body = {}
        if subnet_id:
            body['subnet_id'] = subnet_id
        if port_id:
            body['port_id'] = port_id
        return self.neutron_client.add_interface_router(router_id, body)

    def router_interface_delete(self, router_id, subnet_id=None, port_id=None):
        body = {}
        if subnet_id:
            body['subnet_id'] = subnet_id
        if port_id:
            body['port_id'] = port_id
        self.neutron_client.remove_interface_router(router_id, body)

    def router_add_gateway(self, router_id, network_id):
        body = {'network_id': network_id}
        return self.neutron_client.add_gateway_router(router_id, body)

    def router_remove_gateway(self, router_id):
        self.neutron_client.remove_gateway_router(router_id)

    def router_static_route_list(self, router_id=None):
        routes = self.router_get(router_id).get("routes")
        return routes

    def router_static_route_remove(self, router_id, route_ids):
        currentroutes = self.router_static_route_list(router_id=router_id)
        newroutes = []
        for oldroute in currentroutes:
            if oldroute not in route_ids:
                newroutes.append({'nexthop': oldroute.get("nexthop"),
                                  'destination': oldroute.get("destination")})
        body = {'routes': newroutes}
        new = self.router_update(router_id, **body)
        return new

    def router_static_route_add(self, router_id, newroute):
        body = {}
        currentroutes = self.router_static_route_list(router_id=router_id)
        body['routes'] = [newroute] + [{'nexthop': r.get("nexthop"),
                                        'destination': r.get("destination")}
                                       for r in currentroutes]
        new = self.router_update(router_id, **body)
        return new

    def port_create(self, network_id, **kwargs):
        LOG.debug("port_create(): netid=%s, kwargs=%s" % (network_id, kwargs))
        # In the case policy profiles are being used, profile id is needed.
        if 'policy_profile_id' in kwargs:
            kwargs['n1kv:profile'] = kwargs.pop('policy_profile_id')
        kwargs = unescape_port_kwargs(**kwargs)
        body = {'port': {'network_id': network_id}}
        # if 'tenant_id' not in kwargs:
        #     kwargs['tenant_id'] = self._get_tenant_id()
        body['port'].update(kwargs)
        return self.neutron_client.create_port(body=body).get('port')

    def port_get(self, port_id, **params):
        LOG.debug("port_get(): portid=%(port_id)s, params=%(params)s",
                  {'port_id': port_id, 'params': params})
        return self.neutron_client.show_port(port_id, **params).get('port')

    def port_list(self, **params):
        LOG.debug("port_list(): params=%s", params)
        return self.neutron_client.list_ports(**params).get('ports')

    def port_update(self, port_id, **kwargs):
        LOG.debug("port_update(): portid=%s, kwargs=%s" % (port_id, kwargs))
        kwargs = unescape_port_kwargs(**kwargs)
        body = {'port': kwargs}
        return self.neutron_client.update_port(port_id, body=body).get('port')

    def port_delete(self, port_id):
        self.neutron_client.delete_port(port_id)

    def _sg_name_dict(self, sg_id, rules):
        """Create a mapping dict from secgroup id to its name."""
        related_ids = set([sg_id])
        related_ids |= set(filter(None, [r['remote_group_id'] for r in rules]))
        related_sgs = self.neutron_client.list_security_groups(id=related_ids,
                                                               fields=['id', 'name'])
        related_sgs = related_sgs.get('security_groups')
        return dict((sg['id'], sg['name']) for sg in related_sgs)

    def _security_group_list(self, **filters):
        return self.neutron_client.list_security_groups(**filters).get('security_groups')

    def security_group_list(self, tenant_id=None):
        return self._security_group_list()

    def get_security_group(self, sg_id):
        secgroup = self.neutron_client.show_security_group(sg_id).get('security_group')
        return self._sg_name_dict(sg_id, secgroup['security_group_rules'])

    def get_security_group_by_name(self, sg_name):
        sgs = self.security_group_list()
        for sg in sgs:
            if sg.get("name") == sg_name:
                return sg
        return None

    def delete_security_group(self, sg_id):
        self.neutron_client.delete_security_group(sg_id)

    def list_by_instance(self, instance_id):
        """Gets security groups of an instance."""
        ports = self.port_list(device_id=instance_id)
        sg_ids = []
        for p in ports:
            sg_ids += p.security_groups
        return self._security_group_list(id=set(sg_ids)) if sg_ids else []

    def update_instance_security_group(self, instance_id,
                                       new_security_group_names):
        sg_ids = []
        for sg_name in new_security_group_names:
            sg = self.get_security_group_by_name(sg_name)
            if sg:
                sg_ids.append(sg.get("id"))
        ports = self.port_list(device_id=instance_id)
        for p in ports:
            params = {'security_groups': sg_ids}
            self.port_update(p.get("id"), **params)

    def _get_instance_type_from_device_owner(self, device_owner):
        for key, value in self.device_owner_map.items():
            if device_owner.startswith(key):
                return value
        return device_owner

    def _set_instance_info(self, fip, port=None):
        if fip['port_id']:
            if not port:
                port = self.port_get(fip['port_id'])
            fip['instance_id'] = port["device_id"]
            fip['instance_type'] = self._get_instance_type_from_device_owner(
                port["device_owner"])
        else:
            fip['instance_id'] = None
            fip['instance_type'] = None

    def floating_ip_pools_list(self):
        search_opts = {'router:external': True}
        # return [FloatingIpPool(pool) for pool
        #         in self.neutron_client.list_networks(**search_opts).get('networks')]
        return self.neutron_client.list_networks(**search_opts).get('networks')

    def floating_ip_associate(self, floating_ip_id, port_id):
        pid, ip_address = port_id.split('_', 1)
        update_dict = {'port_id': pid,
                       'fixed_ip_address': ip_address}
        return self.neutron_client.update_floatingip(
            floating_ip_id, {'floatingip': update_dict}).get('floatingip')

    def floating_ip_disassociate(self, floating_ip_id):
        update_dict = {'port_id': None}
        return self.neutron_client.update_floatingip(
            floating_ip_id, {'floatingip': update_dict}).get('floatingip')

    def floating_ip_get(self, floating_ip_id):
        fip = self.neutron_client.show_floatingip(floating_ip_id).get('floatingip')
        self._set_instance_info(fip)
        # return FloatingIp(fip)
        return fip

    def floating_ip_list(self, all_tenants=True, **search_opts):
        if not all_tenants:
            tenant_id = self._get_tenant_id()
            # In Neutron, list_floatingips returns Floating IPs from
            # all tenants when the API is called with admin role, so
            # we need to filter them with tenant_id.
            search_opts['tenant_id'] = tenant_id
            port_search_opts = {'tenant_id': tenant_id}
        else:
            port_search_opts = {}
        fips = self.neutron_client.list_floatingips(**search_opts)
        fips = fips.get('floatingips')
        # Get port list to add instance_id to floating IP list
        # instance_id is stored in device_id attribute
        ports = self.port_list(**port_search_opts)
        port_dict = collections.OrderedDict([(p['id'], p) for p in ports])
        for fip in fips:
            self._set_instance_info(fip, port_dict.get(fip['port_id']))
        # return [FloatingIp(fip) for fip in fips]
        return fips

    def floating_ip_allocate(self, pool, tenant_id=None, **params):
        if not tenant_id:
            tenant_id = app_settings.OS_AUTH.get("project_name")
        create_dict = {
            'floating_network_id': pool,
            # 'tenant_id': self._get_tenant_id()
        }
        if 'subnet_id' in params:
            create_dict['subnet_id'] = params['subnet_id']
        if 'floating_ip_address' in params:
            create_dict['floating_ip_address'] = params['floating_ip_address']
        fip = self.neutron_client.create_floatingip(
            {'floatingip': create_dict}).get('floatingip')
        self._set_instance_info(fip)
        return fip

    def floating_ip_release(self, floating_ip_id):
        self.neutron_client.delete_floatingip(floating_ip_id)

    def _target_ports_by_instance(self, instance_id):
        if not instance_id:
            return None
        search_opts = {'device_id': instance_id}
        return self.port_list(**search_opts)

    def get_target_id_by_instance(self, instance_id, target_list=None):
        if target_list is not None:
            targets = [target for target in target_list
                       if target['instance_id'] == instance_id]
            if not targets:
                return None
            return targets[0]['id']
        else:
            # In Neutron one port can have multiple ip addresses, so this
            # method picks up the first one and generate target id.
            ports = self._target_ports_by_instance(instance_id)
            if not ports:
                return None
            return '{0}_{1}'.format(ports[0]["id"],
                                    ports[0]["fixed_ips"][0]['ip_address'])

    def list_target_id_by_instance(self, instance_id, target_list=None):
        if target_list is not None:
            return [target['id'] for target in target_list
                    if target['instance_id'] == instance_id]
        else:
            ports = self._target_ports_by_instance(instance_id)
            return ['{0}_{1}'.format(p["id"], p["fixed_ips"][0]['ip_address'])
                    for p in ports]

    def qos_policy_create(self, **kwargs):
        body = {'policy': kwargs}
        return self.neutron_client.create_qos_policy(body).get("policy")

    def qos_policy_list(self, **kwargs):
        return self.neutron_client.list_qos_policies(**kwargs).get("policies")

    def qos_policy_update(self, policy, **kwargs):
        body = {'policy': kwargs}
        return self.neutron_client.update_qos_policy(policy, body).get("policy")

    def qos_policy_detail(self, policy, **kwargs):
        return self.neutron_client.show_qos_policy(policy, **kwargs).get("policy")

    def qos_policy_delete(self, policy):
        self.neutron_client.delete_qos_policy(policy)

    def qos_bandwidth_limit_rule_create(self, policy, **kwargs):
        body = {'bandwidth_limit_rule': kwargs}
        return self.neutron_client.create_bandwidth_limit_rule(
            policy, body).get("bandwidth_limit_rule")

    def qos_bandwidth_limit_rule_list(self, policy, **kwargs):
        return self.neutron_client.list_bandwidth_limit_rules(
            policy, **kwargs).get("bandwidth_limit_rules")

    def qos_bandwidth_limit_rule_update(self, rule, policy, **kwargs):
        body = {'bandwidth_limit_rule': kwargs}
        return self.neutron_client.update_bandwidth_limit_rule(
            rule, policy, body).get("bandwidth_limit_rule")

    def qos_bandwidth_limit_rule_detail(self, rule, policy, **kwargs):
        return self.neutron_client.show_bandwidth_limit_rule(
            rule, policy, **kwargs).get("bandwidth_limit_rule")

    def qos_bandwidth_limit_rule_delete(self, rule, policy):
        self.neutron_client.delete_bandwidth_limit_rule(rule, policy)

    def firewall_rule_create(self, **kwargs):
        body = {'firewall_rule': kwargs}
        return self.neutron_client.create_fwaas_firewall_rule(
            body).get("firewall_rule")

    def firewall_rule_get(self, rule_id):
        return self.neutron_client.show_fwaas_firewall_rule(
            rule_id).get('firewall_rule')

    def firewall_rule_delete(self, rule_id):
        self.neutron_client.delete_fwaas_firewall_rule(rule_id)

    def firewall_rule_update(self, rule_id, **kwargs):
        body = {'firewall_rule': kwargs}
        return self.neutron_client.update_fwaas_firewall_rule(
            rule_id, body).get('firewall_rule')

    def _rule_list(self, **kwargs):
        return self.neutron_client.list_fwaas_firewall_rules(
            **kwargs).get('firewall_rules')

    def firewall_rule_list(self, **kwargs):
        return self._rule_list(**kwargs)

    def _policy_list(self, expand_rule, **kwargs):
        policies = self.neutron_client.list_fwaas_firewall_policies(
            **kwargs).get('firewall_policies')
        if expand_rule and policies:
            rules = self._rule_list()
            rule_dict = collections.OrderedDict((rule.get("id"), rule) for rule in rules)
            for p in policies:
                p['rules'] = [rule_dict.get(rule) for rule in p['firewall_rules']]
        return policies

    def firewall_policy_list(self, expand_rule=True, **kwargs):
        return self._policy_list(expand_rule, **kwargs)

    def firewall_policy_get(self, policy_id, expand_rule=True):
        policy = self.neutron_client.show_fwaas_firewall_policy(
            policy_id).get('firewall_policy')
        if expand_rule:
            policy_rules = policy['firewall_rules']
            if policy_rules:
                rules = self._rule_list(firewall_policy_id=policy_id)
                rule_dict = collections.OrderedDict((rule.get("id"), rule)
                                                    for rule in rules)
                policy['rules'] = [rule_dict.get(rule) for rule in policy_rules]
            else:
                policy['rules'] = []
        return policy

    def firewall_policy_create(self, **kwargs):
        body = {'firewall_policy': kwargs}
        return self.neutron_client.create_fwaas_firewall_policy(
            body).get('firewall_policy')

    def firewall_policy_update(self, policy_id, **kwargs):
        body = {'firewall_policy': kwargs}
        return self.neutron_client.update_fwaas_firewall_policy(
            policy_id, body).get('firewall_policy')

    def firewall_policy_delete(self, policy_id):
        return self.neutron_client.delete_fwaas_firewall_policy(policy_id)

    def firewall_policy_remove_rule(self, policy_id, **kwargs):
        return self.neutron_client.remove_rule_fwaas_firewall_policy(
            policy_id, kwargs)

    def firewall_policy_insert_rule(self, policy_id, **kwargs):
        return self.neutron_client.insert_rule_fwaas_firewall_policy(
            policy_id, kwargs)

    def firewall_list(self, expand_rule=False, **kwargs):
        return self.neutron_client.list_fwaas_firewall_groups(
            **kwargs).get('firewall_groups')

    def firewall_create(self, **kwargs):
        body = {'firewall_group': kwargs}
        return self.neutron_client.create_fwaas_firewall_group(
            body).get("firewall_group")

    def firewall_delete(self, firewall_id):
        return self.neutron_client.delete_fwaas_firewall_group(firewall_id)

    def firewall_update(self, firewall_id, **kwargs):
        body = {'firewall_group': kwargs}
        return self.neutron_client.update_fwaas_firewall_group(
            firewall_id, body).get('firewall_group')

    def firewall_get(self, firewall_id, expand_policy=True):
        firewall_group = self.neutron_client.show_fwaas_firewall_group(
            firewall_id).get("firewall_group")
        if expand_policy:
            ingress_policy_id = firewall_group['ingress_firewall_policy_id']
            if ingress_policy_id:
                firewall_group['ingress_policy'] = self.firewall_policy_get(
                    ingress_policy_id, expand_rule=False)
            else:
                firewall_group['ingress_policy'] = None

            egress_policy_id = firewall_group['egress_firewall_policy_id']
            if egress_policy_id:
                firewall_group['egress_policy'] = self.firewall_policy_get(
                    egress_policy_id, expand_rule=False)
            else:
                firewall_group['egress_policy'] = None
        return firewall_group

    def _is_target(self, port):
        return (port['device_owner'].startswith('compute:') or
                port['device_owner'].startswith('network:router_interface'))

    def fwg_port_list_for_tenant(self, **kwargs):
        # kwargs['tenant_id'] = self._get_tenant_id()
        ports = self.port_list(**kwargs)
        fwgs = self.firewall_list()
        fwg_ports = []
        for fwg in fwgs:
            if not fwg['ports']:
                continue
            fwg_ports += fwg['ports']
        return [p for p in ports
                if self._is_target(p) and p['id'] not in fwg_ports]

    def floatingips_list(self):
        return self.neutron_client.list_floatingips()

    def agent_list(self):
        return self.neutron_client.list_agents()

    def create_portmapping(self, port_id, proto, instance_port):
        body = {
            'portmapping': {
                'port_id': port_id,
                'proto': proto,
                'instance_port': instance_port
            }
        }
        return self.neutron_client.create_portmapping(body)

    def delete_portmapping(self, id):
        return self.neutron_client.delete_portmapping(id)

    def list_portmappings(self):
        return self.neutron_client.list_portmappings()

    def show_portmapping(self, id, **_params):
        return self.neutron_client.show_portmapping(id)

    def _complete_uuid(self, obj_id):
        return "{}{}".format(obj_id.zfill(4), str(uuid.uuid4())[4:])

    def create_switch_vlan(self, **kwargs):
        # vlan_id, netmask, gateway, interfaces
        sv = {'vlan_id': kwargs.get("vlan_id")}
        if kwargs.get("netmask"):
            sv.update({'netmask': kwargs.get("netmask")})
        if kwargs.get("gateway"):
            sv.update({'gateway': kwargs.get("gateway")})
        if kwargs.get("interface_id"):
            sv.update({'interfaces': {"interface_id": kwargs.get("interface_id")}})

        return self.neutron_client.create_switch_vlan({'switch_vlan': sv}).get("switch_vlan")

    @complete_uuid("vlan_id")
    def delete_switch_vlan(self, vlan_id):
        return self.neutron_client.delete_switch_vlan(vlan_id)

    def list_switch_vlans(self, **kwargs):
        return self.neutron_client.list_switch_vlans(**kwargs).get("switch_vlans")

    @complete_uuid("vlan_id")
    def get_switch_vlan(self, vlan_id):
        return self.neutron_client.show_switch_vlan(vlan_id).get("switch_vlan")

    def config_switch_interface(self, **kwargs):
        # interface_id, module_id=0, switch_id=0, permit_vlan=1, type="access"
        si = {'interface_id': kwargs.get("interface_id"),
              'type': kwargs.get("type") or 'access'}
        if kwargs.get("module_id"):
            si.update({'module_id': kwargs.get("module_id")})
        if kwargs.get("switch_id"):
            si.update({'switch_id': kwargs.get("switch_id")})
        if kwargs.get("permit_vlan"):
            si.update({'permit_vlan': kwargs.get("permit_vlan")})
        return self.neutron_client.create_switch_interface({'switch_interface': si}).get("switch_interface")

    @complete_uuid("interface_id")
    def undo_switch_interface_config(self, interface_id):
        return self.neutron_client.delete_switch_interface(interface_id)

    def list_switch_interfaces(self, **kwargs):
        return self.neutron_client.list_switch_interfaces(**kwargs).get("switch_interfaces")

    @complete_uuid("interface_id")
    def get_switch_interface(self, interface_id):
        return self.neutron_client.show_switch_interface(interface_id).get("switch_interface")


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="L5uCdcjQQuyY9DLs", project_name="admin",
                 user_domain_id="default", project_domain_id="default")
    aaa = cli.port_get("ff2d0b99-eb06-486d-83be-31978257c3a9")
    vlan_id = "1001"
    cidr = "10.98.198.0/24"
    gateway = "10.98.198.254"
    netmask = cidr.split("/")[-1]
    params = {'name': "Vlan{}".format(vlan_id),
              'admin_state_up': "True",
              'shared': True,
              'router:external': False,
              'provider:network_type': "vlan",
              'provider:physical_network': "vlanprovider",
              'provider:segmentation_id': vlan_id}
    net = cli.network_create(**params)
    net = cli.network_get(net.get("id"))
    subnet = cli.subnet_create(net.get("id"), name="{}-subnet".format(net.get("name")),
                               cidr=cidr, gateway_ip=gateway)
    vlan2 = cli.create_switch_vlan(vlan_id=vlan_id, gateway=gateway, netmask=netmask, interface_id=["36", "37"])
    # vlans = cli.list_switch_vlans()
    # cli.undo_switch_interface_configure(interface_id="36")
    # cli.undo_switch_interface_configure(interface_id="37")
    vlan1 = cli.get_switch_vlan("1001")
    cli.delete_switch_vlan("1001")
    cli.subnet_delete(subnet_id=subnet.get("id"))
    cli.network_delete(net.get("id"))
    # vlan1 = cli.get_switch_vlan("1001")

    # ifs = cli.list_switch_interfaces()
    # if1 = cli.get_switch_interface("36")
    # cli.undo_switch_interface_configure(interface_id="36")
    # if1 = cli.get_switch_interface("36")
    cli.config_switch_interface(interface_id="36", permit_vlan="1001", type='access')
    if1 = cli.get_switch_interface("36")
    cli.undo_switch_interface_config(interface_id="36")

    net = cli.network_get("14f32aab-85d2-44dd-9b9c-faa8f459173f")
    ports = cli.port_list()
    port = cli.port_create("13e1a7cd-010c-4713-9f0a-bbbcb55aa9f4",
                           **{"port_security_enabled": False,
                              "admin_state_up": True})
    port = cli.port_create("13e1a7cd-010c-4713-9f0a-bbbcb55aa9f4",
                           **{"port_security_enabled": False,
                              "admin_state_up": True,
                              "fixed_ips": [{"ip_address": "10.98.98.221"}]})
    cli.port_delete(port.get("id"))
    # fips = cli.floating_ip_list()
    # print fips
    # protocol action source_ip_address destination_ip_address source_port
    # destination_port ip_version shared enabled
    # fwrs = cli.firewall_rule_list()
    # fwr = cli.firewall_rule_create(name="2123123", protocol="tcp", action="allow")
    # print fwrs
    # fws = cli.firewall_rule_get(fwr.get("id"))
    # cli.firewall_rule_update(fwr.get("id"), shared=True)
    # cli.firewall_rule_delete(fwr.get("id"))

    # fwps = cli.firewall_policy_list()
    # print fwps
    # fwp = cli.firewall_policy_create(name="233233")
    # fwp = cli.firewall_policy_get(fwp.get("id"))
    # cli.firewall_policy_update(fwp.get("id"), name="23333245", shared=True)
    # cli.firewall_policy_insert_rule(fwp.get("id"), firewall_rule_id=fws.get("id"), insert_before="", insert_after="")
    # cli.firewall_policy_remove_rule(fwp.get("id"), firewall_rule_id=fws.get("id"))
    # cli.firewall_policy_delete(fwp.get("id"))

    # fws = cli.firewall_list()
    # fw = cli.firewall_create(name="fw111")
    # fw = cli.firewall_get(fw.get("id"))
    # cli.firewall_update(fw.get("id"), name="fw2233", admin_state_up=True)
    # cli.firewall_update(fw.get("id"), ingress_firewall_policy_id="9cb21980-2e2d-4515-b3c7-30a6771bfe8b")
    # cli.firewall_delete(fw.get("id"))
    # print fws

    qp = cli.qos_policy_create(name="12321")

    qps = cli.qos_policy_list()
    #
    # qp = cli.qos_policy_update(policy=qp.get("id"), name="123123123345")
    #
    qp = cli.qos_policy_detail(policy=qp.get("id"))

    # qprs = cli.qos_bandwidth_limit_rule_list("d3499b26-806d-43dd-80f1-68f0787af486")
    #
    # qprin = cli.qos_bandwidth_limit_rule_create(policy=qp.get("id"), max_kbps=300,
    #                                             max_burst_kbps=300, direction="ingress")
    # qpre = cli.qos_bandwidth_limit_rule_create(policy=qp.get("id"), max_kbps=200,
    #                                            max_burst_kbps=200, direction="egress")
    #
    # qprin = cli.qos_bandwidth_limit_rule_detail(qprin.get("id"), qp.get("id"))
    #
    # qpre = cli.qos_bandwidth_limit_rule_update(qpre.get("id"), qp.get("id"), max_kbps=3000)
    #
    # cli.qos_bandwidth_limit_rule_delete(qprin.get("id"), qp.get("id"))
    # cli.qos_bandwidth_limit_rule_delete(qpre.get("id"), qp.get("id"))
    #
    cli.qos_policy_delete(qp.get("id"))
