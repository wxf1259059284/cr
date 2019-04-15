from __future__ import unicode_literals

import functools
import logging
import time

from django.core.cache import cache
from django.utils.translation import ugettext as _

from neutronclient.common.exceptions import Conflict

from base.utils.functional import cached_property
from base_cloud.clients.neutron_client import Client as nt_client
from base_cloud.exception import FriendlyException
from base_cloud import app_settings


LOG = logging.getLogger(__name__)
EXTERNAL_NET_ID = "external_network_id"
ATTEMPTS = 900


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        LOG.debug("Start {}(): args={}, kwargs={}".format(func_name,
                                                          args, kwargs))
        ff = func(self, *args, **kwargs)
        LOG.debug("End {}()".format(func_name))
        return ff
    return wrapper


class NetworkAction(object):
    def __init__(self):
        super(NetworkAction, self).__init__()

    @cached_property
    def neutron_cli(self):
        return nt_client()

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        raise FriendlyException(err_msg)

    @logger_decorator
    def load_available_fips_dict(self, exclude_list=None):
        if not exclude_list:
            exclude_list = []
        avialable_fips = {}
        fips = self.neutron_cli.floating_ip_list()
        for fip in fips:
            fip_addr = fip.get("floating_ip_address")
            if not fip.get("instance_id") and fip_addr not in exclude_list:
                avialable_fips.update({fip_addr: fip.get("id")})
        return avialable_fips

    def get_fip(self, fip_id=None, fip_addr=None):
        try:
            if fip_id:
                fip = self.neutron_cli.floating_ip_get(fip_id)

            return fip
        except Exception as e:
            err_msg = _("Unable to get floating ip.")
            self._handle_error(err_msg, e)
        return None

    @logger_decorator
    def create_fip(self, ip_addr=None):
        try:
            pool_id = cache.get("external_net_pool_id")
            if not pool_id:
                pool_id = self.neutron_cli.floating_ip_pools_list()[0].get("id")
                cache.set("external_net_pool_id", pool_id, 3600*24)
        except Exception as e:
            err_msg = _("Unable to retrieve floating IP pools.")
            self._handle_error(err_msg, e)

        try:
            if ip_addr:
                return self.neutron_cli.floating_ip_allocate(
                                pool_id, floating_ip_address=ip_addr)
            return self.neutron_cli.floating_ip_allocate(pool_id)
        except Exception as e:
            err_msg = _("Unable to create floating ip.")
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_fip(self, fip_id, sync=True):
        try:
            self.neutron_cli.floating_ip_release(fip_id)
        except Exception as e:
            err_msg = _("Unable to release floating ip {}.").format(fip_id)
            self._handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.neutron_cli.floating_ip_get(fip_id)
                except Exception as e:
                    LOG.info("Deleted floating ip {}".format(fip_id))
                    break
                attempts -= 1
                time.sleep(1)
        return True

    @logger_decorator
    def bind_fip(self, fip, port=None, instance=None):
        type = "port" if port else "instance"
        try:
            port_id = port or self.neutron_cli.get_target_id_by_instance(instance.id)
            fip_obj = self.neutron_cli.floating_ip_associate(fip,
                                                             port_id)
            LOG.info("Bind floating ip {} to {} {}.".format(
                            fip, type, port or instance.id))
            return fip_obj
        except Exception as e:
            err_msg = _("Unable to bind fip {} for {} {}").format(
                            fip, type, port or instance.id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_network(self, **kwargs):
        prefix = kwargs.pop("prefix") if "prefix" in kwargs else None
        try:
            networks = self.neutron_cli.network_get_all(**kwargs)
        except Exception as e:
            err_msg = _("Unable to retrieve network list.")
            self._handle_error(err_msg, e)
        if prefix and networks:
            return [net for net in networks
                    if net.get("name").startswith(prefix.strip())]
        return networks

    def get_network(self, network_id):
        try:
            network = self.neutron_cli.network_get(network_id)
            return network
        except Exception as e:
            err_msg = _("Unable to get network ({}).").format(network_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_network_by_name(self, network_name):
        try:
            return self.neutron_cli.network_list_by_name(network_name)
        except Exception as e:
            err_msg = _("Unable to retrieve network list.")
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_router(self, **kwargs):
        prefix = kwargs.pop("prefix") if "prefix" in kwargs else None
        try:
            routers = self.neutron_cli.router_get_all()
        except Exception as e:
            err_msg = _("Unable to retrieve router list.")
            self._handle_error(err_msg, e)
        if prefix and routers:
            return [router for router in routers
                    if router.get("name").startswith(prefix.strip())]
        return routers

    @logger_decorator
    def create_network(self, **kwargs):
        """Create a network

        :param name: name for network
        :param admin_state_up:
        :param shared: share with other project
        :return: Network object
        """
        name = kwargs.get("name")
        try:
            network = self.neutron_cli.network_create(**kwargs)
            LOG.info("Created network {} .".format(name))
            return network
        except Exception as e:
            err_msg = _("Unable to create network {}".format(name))
            self._handle_error(err_msg, e)

    @logger_decorator
    def check_network_status(self, net_id):
        attempts = ATTEMPTS
        while attempts:
            if attempts <= 0:
                err_msg = _("Failed to check status for network {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(net_id)
                break
            try:
                network = self.neutron_cli.network_get(net_id)
                if network.get("status") == "ACTIVE":
                    return True
            except Exception as e:
                err_msg = "Unable to check network ({}) status".format(net_id)
                self._handle_error(err_msg, e)
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    @logger_decorator
    def create_subnet(self, net_id, **kwargs):
        """Create a subnet

        :param net_id: network id
        :param name: name for subnet
        :param cidr: cidr for subnet : 192.168.1.0/24
        :param enable_dhcp: weather enable dhcp
        :param dns_nameservers: dns_nameservers for subnet
        :return: Subnet object
        """
        name = kwargs.get("name")
        cidr = kwargs.get("cidr")

        try:
            subnet = self.neutron_cli.subnet_create(net_id, **kwargs)
            LOG.info("Subnet {} with cidr{} created.".format(name, cidr))
            return subnet
        except Exception as e:
            if e.message.find("overlaps with another subnet.") >= 0:
                err_msg = _("Network {} with cidr {} already "
                            "exists.").format(net_id, cidr)
            else:
                err_msg = _("Unable to create subnet {} with "
                            "cidr {}.").format(name, cidr)
            self._handle_error(err_msg, e)

    @logger_decorator
    def update_subnet(self, subnet_id, **kwargs):
        params = {}

        if kwargs.get("name"):
            params['name'] = kwargs.get("name")

        if kwargs.get('no_gateway'):
            params['gateway_ip'] = None
        elif kwargs.get('gateway_ip'):
            params['gateway_ip'] = kwargs.get('gateway_ip')

        subnet = self.neutron_cli.subnet_get(subnet_id)
        if kwargs.get('gateway_ip') == subnet.get("gateway_ip"):
            del params['gateway_ip']

        if kwargs.get("enable_dhcp") is not None:
            params['enable_dhcp'] = kwargs.get("enable_dhcp")

        if kwargs.get("allocation_pools"):
            pools = [dict(zip(['start', 'end'], pool.strip().split(',')))
                     for pool in kwargs.get("allocation_pools", "").splitlines()
                     if pool.strip()]
            params['allocation_pools'] = pools

        if kwargs.get('dns_nameservers'):
            nameservers = [ns.strip()
                           for ns in kwargs.get('dns_nameservers', "").splitlines()
                           if ns.strip()]
            params['dns_nameservers'] = nameservers

        if kwargs.get('host_routes'):
            routes = [dict(zip(['destination', 'nexthop'],
                               route.strip().split(',')))
                      for route in kwargs.get('host_routes', "").splitlines()
                      if route.strip()]
            params['host_routes'] = routes

        try:
            subnet = self.neutron_cli.subnet_update(subnet_id, **params)
            LOG.info("Subnet {} updated.".format(subnet_id))
            return subnet
        except Exception as e:
            err_msg = _("Unable to update subnet {} with "
                        "params {}.").format(subnet_id, kwargs)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_external_net_id(self):
        ext_net_id = cache.get(EXTERNAL_NET_ID)
        if not ext_net_id:
            ext_nets = self.neutron_cli.ext_networks_list()
            if ext_nets:
                ext_net_id = ext_nets[0].get("id")
                cache.set(EXTERNAL_NET_ID, ext_net_id)
        return ext_net_id

    @logger_decorator
    def create_router(self, **kwargs):
        name = kwargs.get("name")
        try:
            router = self.neutron_cli.router_create(name=name,
                                                    admin_state_up=True)
            LOG.info("Created router {} .".format(name))
            return router
        except Exception as e:
            err_msg = _("Unable to create router {}.").format(name)
            self._handle_error(err_msg, e)

    @logger_decorator
    def add_static_route(self, router_id, newroute):
        try:
            self.neutron_cli.router_static_route_add(router_id,
                                                     newroute)
        except Exception as e:
            err_msg = _("Unable to add static route "
                        "for router {}.").format(router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def remove_static_route(self, router_id, route_ids):
        try:
            self.neutron_cli.router_static_route_remove(router_id,
                                                        route_ids)
        except Exception as e:
            err_msg = _("Unable to remove static route "
                        "for router {}.").format(router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_static_routes(self, router_id):
        try:
            return self.neutron_cli.router_static_route_list(router_id)
        except Exception as e:
            err_msg = _("Unable to list static route "
                        "for router {}.").format(router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_port(self, port_id):
        try:
            self.neutron_cli.port_delete(port_id)
        except Exception as e:
            err_msg = _("Unable to delete port {}.").format(port_id)
            self._handle_error(err_msg, e)

    def create_port(self, network_id, **kwargs):
        try:
            port = self.neutron_cli.port_create(network_id, **kwargs)
            LOG.info("Created port {} in "
                     "network {}.".format(port.get("id"), network_id))
        except Exception as e:
            err_msg = _("Unable to create port in "
                        "network {}.").format(network_id)
            self._handle_error(err_msg, e)
        return port

    def get_port(self, port_id):
        try:
            return self.neutron_cli.port_get(port_id)
        except Exception as e:
            err_msg = _("Unable to get port {}.").format(port_id)
            self._handle_error(err_msg, e)

    def _generate_gw_addr(self, subnet_id):
        subnet = self.neutron_cli.subnet_get(subnet_id)
        cidr_net_seg = subnet.get("cidr")[:-4]

        ports = self.neutron_cli.port_list(network_id=subnet.get("network_id"))
        used_ips = []
        for port in ports:
            for fixed_ip in port.get("fixed_ips"):
                used_ips.append(fixed_ip.get("ip_address"))

        gw_addr = 254
        while gw_addr > 0:
            gw_ip = "{}{}".format(cidr_net_seg, gw_addr)
            if gw_ip not in used_ips:
                return gw_ip
            gw_addr -= 1
        err_msg = _("Unable to generate gateway ip "
                    "address for subnet {}").format(subnet_id)
        self._handle_error(err_msg)

    def _add_interface_by_port(self, router_id, subnet_id, ip_address):
        try:
            subnet = self.neutron_cli.subnet_get(subnet_id)
        except Exception as e:
            err_msg = _('Unable to get subnet {}').format(subnet_id)
            self._handle_error(err_msg, e)

        try:
            body = {'network_id': subnet.get("network_id"),
                    'fixed_ips': [{'subnet_id': subnet.get("id"),
                                   'ip_address': ip_address}]}
            port = self.neutron_cli.port_create(**body)
        except Exception as e:
            err_msg = _('Unable to create port for subnet {}.').forrmat(subnet_id)
            self._handle_error(err_msg, e)

        try:
            self.neutron_cli.router_interface_add(router_id,
                                                  port_id=port.get("id"))
        except Exception as e:
            err_msg = _('Unable to bind port {} to '
                        'router {} .').format(port.get("id"), router_id)
            self.delete_port(port)
            self._handle_error(err_msg, e)
        return port

    @logger_decorator
    def router_bind_subnet(self, router_id, subnet_id):
        try:
            self.neutron_cli.router_interface_add(router_id,
                                                  subnet_id=subnet_id)
            LOG.info("Connected subnet {} to "
                     "router {} .".format(subnet_id, router_id))
        except Conflict:
            self._add_interface_by_port(router_id, subnet_id,
                                        self._generate_gw_addr(subnet_id))
        except Exception as e:
            err_msg = _("Unable to connect subnet {} "
                        "to router {}.").format(subnet_id, router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def router_remove_port(self, router_id, port_id):
        try:
            self.neutron_cli.router_interface_delete(router_id,
                                                     port_id=port_id)
            LOG.info("Port {} removed from "
                     "router {} .".format(port_id, router_id))
        except Exception as e:
            err_msg = _("Unable to remove port {} "
                        "from router {}.").format(port_id, router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def router_bind_gateway(self, router_id, ext_net_id):
        try:
            self.neutron_cli.router_add_gateway(router_id, ext_net_id)
            LOG.info("Router {} connected to the extrenal "
                     "network {} .".format(router_id, ext_net_id))
        except Exception as e:
            err_msg = _("Unable to connect external network "
                        "for router {}").format(router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def router_remove_gateway(self, router_id):
        try:
            self.neutron_cli.router_remove_gateway(router_id)
            LOG.info("External gateway removed from "
                     "router {}.".format(router_id))
        except Exception as e:
            err_msg = _("Unable to remove external gateway "
                        "from router {}").format(router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_network(self, network_id, sync=True):
        try:
            self.neutron_cli.network_delete(network_id)
        except Exception as e:
            err_msg = _("Unable to delete network")
            self._handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.neutron_cli.network_get(network_id)
                except Exception as e:
                    LOG.info("Deleted network {}".format(network_id))
                    break
                attempts -= 1
                time.sleep(1)

    @logger_decorator
    def delete_subnet(self, subnet_id, sync=True):
        try:
            self.neutron_cli.subnet_delete(subnet_id)
        except Exception as e:
            err_msg = _("Unable to delete subnet")
            self._handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.neutron_cli.subnet_get(subnet_id)
                except Exception as e:
                    LOG.info("Deleted subnet {}".format(subnet_id))
                    break
                attempts -= 1
                time.sleep(1)

    @logger_decorator
    def delete_router(self, router_id, sync=True):
        try:
            self.neutron_cli.router_delete(router_id)
        except Exception as e:
            err_msg = _("Unable to delete router")
            self._handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.neutron_cli.router_get(router_id)
                except Exception as e:
                    LOG.info("Deleted router {}".format(router_id))
                    break
                attempts -= 1
                time.sleep(1)

    @logger_decorator
    def update_instance_security_group(self, instance_id, groups):
        if groups:
            try:
                self.neutron_cli.update_instance_security_group(instance_id, groups)
                return True
            except Exception as e:
                err_msg = _("Unable to update security group "
                            "for instance {}.").format(instance_id)
                self._handle_error(err_msg, e)
        else:
            err_msg = _("At least one security group for "
                        "instance {}").format(instance_id)
        self._handle_error(err_msg)

    @logger_decorator
    def create_firewall_rule(self, **kwargs):
        """Create a firewall rule

        :param name: name for rule
        :param description: description for rule
        :param protocol: protocol for rule: tcp udp icmp any
        :param action: action for rule: allow deny reject
        :param source_ip_address: source IP address or subnet
        :param source_port: integer in [1, 65535] or range in a:b
        :param destination_ip_address: destination IP address or subnet
        :param destination_port: integer in [1, 65535] or range in a:b
        :param shared: boolean (default false)
        :param enabled: boolean (default true)
        :return: Rule object
        """
        try:
            return self.neutron_cli.firewall_rule_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create firewall rule")
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_firewall_rules(self, rules):
        fw_rules = []
        for rule in rules:
            try:
                rule = self.create_firewall_rule(**rule)
                fw_rules.append(rule)
            except Exception as e:
                err_msg = _("Unable to create firewall "
                            "rule {}.").format(rule.get("name"))
                self._handle_error(err_msg, e)
        return fw_rules

    @logger_decorator
    def delete_firewall_rule(self, rule_id, is_async=True):
        try:
            self.neutron_cli.firewall_rule_delete(rule_id)
            if not is_async:
                while 1:
                    try:
                        self.neutron_cli.firewall_rule_get(rule_id)
                        time.sleep(1)
                        continue
                    except Exception:
                        LOG.debug("Deleted firewall rule {}".format(rule_id))
                    break
        except Exception as e:
            err_msg = _("Unable to delete firewall rule")
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_firewall_policy(self, **kwargs):
        """Create a firewall policy

            :param name: name for policy
            :param description: description for policy
            :param firewall_rules: ordered list of rules in policy
            :param shared: boolean (default false)
            :param audited: boolean (default false)
            :return: Policy object
            """
        try:
            return self.neutron_cli.firewall_policy_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create firewall policy")
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_firewall_policy(self, policy_id):
        try:
            self.neutron_cli.firewall_policy_delete(policy_id)
        except Exception as e:
            err_msg = _("Unable to delete firewall policy")
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_firewall_policy(self, policy_id, expand_rule=True):
        try:
            return self.neutron_cli.firewall_policy_get(policy_id, expand_rule)
        except Exception as e:
            err_msg = _("Unable to delete firewall policy")
            self._handle_error(err_msg, e)

    def _rule_compare(self, rule1, rule2):
        for key, value in rule2.items():
            if rule1.get(key) != value:
                return False
        return True

    def get_firewall_rule_by_params(self, policy, rule):
        rules = self.get_firewall_policy(policy.get("id")).get("rules")

        for r in rules:
            if self._rule_compare(r, rule):
                return r
        return {}

    @logger_decorator
    def remove_firewall_policy_rule(self, policy_id, **kwargs):
        try:
            self.neutron_cli.firewall_policy_remove_rule(policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to remove firewall policy rule")
            self._handle_error(err_msg, e)

    @logger_decorator
    def insert_firewall_policy_rule(self, policy_id, **kwargs):
        try:
            self.neutron_cli.firewall_policy_insert_rule(policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to insert firewall policy rule")
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_firewall(self, **kwargs):
        prefix = kwargs.pop("prefix") if "prefix" in kwargs else None
        try:
            firewalls = self.neutron_cli.firewall_list(**kwargs)
        except Exception as e:
            err_msg = _("Unable to retrieve firewall list")
            self._handle_error(err_msg, e)
        if prefix and firewalls:
            return [firewall for firewall in firewalls
                    if firewall.get("name").startswith(prefix.strip())]
        return firewalls

    @logger_decorator
    def create_firewall(self, **kwargs):
        """Create a firewall for specified policy

            :param name: name for firewall
            :param description: description for firewall
            :param firewall_policy_id: policy id used by firewall
                      ingress_firewall_policy_id
                      egress_firewall_policy_id
            :param shared: boolean (default false)
            :param admin_state_up: boolean (default true)
            :param ports
            :return: Firewall object
            """
        try:
            return self.neutron_cli.firewall_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create firewall")
            self._handle_error(err_msg, e)

    @logger_decorator
    def update_firewall(self, firewall_id, **kwargs):
        try:
            return self.neutron_cli.firewall_update(firewall_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to update firewall {}").format(firewall_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_firewall(self, firewall_id):
        try:
            self.neutron_cli.firewall_delete(firewall_id)
        except Exception as e:
            err_msg = _("Unable to delete firewall {}").format(firewall_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_firewall(self,  firewall_id, expand_policy=True):
        try:
            return self.neutron_cli.firewall_get(firewall_id, expand_policy)
        except Exception as e:
            err_msg = _("Unable to get firewall {}").format(firewall_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def check_firewall_status(self, firewall_id, break_status="ACTIVE"):

        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Failed to check status for firewall {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(firewall_id)
                break
            firewall = self.get_firewall(firewall_id)
            if firewall.get("status") == break_status:
                msg = "Firewall {} status {}.".format(firewall_id, break_status)
                LOG.info(msg)
                return firewall
            elif firewall.get("status") == "ERROR":
                err_msg = _("Firewall {} Status Error.").format(firewall_id)
                break
            LOG.debug("Firewall status not in {}. "
                      "Try again 1 second later...".format(break_status))
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    @logger_decorator
    def list_qos_policy(self, **kwargs):
        prefix = kwargs.pop("prefix") if "prefix" in kwargs else None
        try:
            policies = self.neutron_cli.qos_policy_list(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create qos policy")
            self._handle_error(err_msg, e)

        if prefix and policies:
            return [policy for policy in policies
                    if policy.get("name").startswith(prefix.strip())]
        return policies

    @logger_decorator
    def create_qos_policy(self, **kwargs):
        try:
            return self.neutron_cli.qos_policy_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create qos policy")
            self._handle_error(err_msg, e)

    @logger_decorator
    def update_qos_policy(self, policy_id, **kwargs):
        try:
            return self.neutron_cli.qos_policy_update(policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to update qos policy {}").format(policy_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_qos_policy(self, policy_id):
        try:
            self.neutron_cli.qos_policy_delete(policy_id)
        except Exception as e:
            err_msg = _("Unable to delete qos policy")
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_qos_policy(self, policy_id, **kwargs):
        try:
            return self.neutron_cli.qos_policy_detail(policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to get qos policy {}").format(policy_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_qos_bandwidth_limit_rules(self, policy_id, **kwargs):
        try:
            return self.neutron_cli.qos_bandwidth_limit_rule_list(policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to list qos bandwidth limit rules")
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_qos_bandwidth_limit_rule(self, policy_id, **kwargs):
        try:
            return self.neutron_cli.qos_bandwidth_limit_rule_create(policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to create qos bandwidth limit rule")
            self._handle_error(err_msg, e)

    def update_qos_bandwidth_limit_rule(self, rule_id, policy_id, **kwargs):
        try:
            return self.neutron_cli.qos_bandwidth_limit_rule_update(rule_id, policy_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to create qos bandwidth limit rule {}").format(rule_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_qos_bandwidth_limit_rule(self, rule_id, policy_id):
        try:
            self.neutron_cli.qos_bandwidth_limit_rule_delete(rule_id, policy_id)
        except Exception as e:
            err_msg = _("Unable to delete qos bandwidth limit rule {}").format(rule_id)
            self._handle_error(err_msg, e)

    def bind_port_qos_policy(self, port_id, policy_id):
        try:
            self.neutron_cli.port_update(
                        port_id, qos_policy_id=policy_id)
        except Exception as e:
            err_msg = _("Unable to bind qos policy {} "
                        "to port {}").format(policy_id, port_id)
            self._handle_error(err_msg, e)

    def bind_ports_qos_policy(self, port_ids, policy_id):
        for port_id in port_ids:
            self.bind_port_qos_policy(port_id, policy_id)

    @logger_decorator
    def get_subnet_by_network_id(self, network_id):
        try:
            return self.neutron_cli.subnet_get_by_network_id(network_id)
        except Exception as e:
            err_msg = _("Unable to get subnet {}").format(network_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_subnet_detail(self, subnet_id):
        try:
            return self.neutron_cli.subnet_get(subnet_id)
        except Exception as e:
            err_msg = _("Unable to get subnet {}").format(subnet_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_subnet(self):
        try:
            return self.neutron_cli.subnet_get_all()
        except Exception as e:
            err_msg = _("Unable to get subnet {}").format('all')
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_router(self, router_id):
        try:
            return self.neutron_cli.router_get(router_id)
        except Exception as e:
            err_msg = _("Unable to get router {}").format(router_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_floating_ip(self, **params):
        try:
            return self.neutron_cli.floating_ip_list(**params)
        except Exception as e:
            err_msg = _("Unable to get floating_ip")
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_firewall_rule(self):
        try:
            return self.neutron_cli.firewall_rule_list()
        except Exception as e:
            err_msg = _("Unable to get firewall_rule list")
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_firewall_rule(self, rule_id):
        try:
            return self.neutron_cli.firewall_rule_get(rule_id)
        except Exception as e:
            err_msg = _("Unable to get firewall_rule")
            self._handle_error(err_msg, e)

    def list_all_floatingips(self):
        try:
            return self.neutron_cli.floating_ip_list()
        except Exception as e:
            err_msg = _("Unable to get floating_ip_list")
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_switch_vlans(self):
        try:
            return self.neutron_cli.list_switch_vlans()
        except Exception as e:
            err_msg = _("Unable to list vlans on switch")
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_switch_vlan(self, vlan_id):
        try:
            return self.neutron_cli.get_switch_vlan(vlan_id)
        except Exception as e:
            err_msg = _("Unable to get vlan ({}) on switch".format(vlan_id))
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_switch_vlan(self, vlan_id):
        try:
            return self.neutron_cli.delete_switch_vlan(vlan_id)
        except Exception as e:
            err_msg = _("Unable to delete vlan ({}) "
                        "on switch".format(vlan_id))
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_switch_vlan(self, vlan_id, gateway=None,
                           netmask=None, interface_id=None):
        try:
            return self.neutron_cli.create_switch_vlan(vlan_id=vlan_id,
                                                       gateway=gateway,
                                                       netmask=netmask,
                                                       interface_id=interface_id)
        except Exception as e:
            err_msg = _("Unable to create vlan ({}) "
                        "on switch".format(vlan_id))
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_switch_interfaces(self):
        try:
            return self.neutron_cli.list_switch_interfaces()
        except Exception as e:
            err_msg = _("Unable to list interfaces on switch")
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_switch_interface(self, interface_id):
        try:
            return self.neutron_cli.get_switch_interface(interface_id)
        except Exception as e:
            err_msg = _("Unable to get interface ({}) "
                        "on switch".format(interface_id))
            self._handle_error(err_msg, e)

    @logger_decorator
    def undo_switch_interface_config(self, interface_id):
        try:
            return self.neutron_cli.undo_switch_interface_config(interface_id)
        except Exception as e:
            err_msg = _("Unable to undo interface ({}) "
                        "configuration on switch".format(interface_id))
            self._handle_error(err_msg, e)

    @logger_decorator
    def config_switch_interface(self, interface_id, permit_vlan, type='access'):
        try:
            return self.neutron_cli.config_switch_interface(interface_id, permit_vlan, type)
        except Exception as e:
            err_msg = _("Unable to config interface ({}) "
                        "on switch".format(interface_id))
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_vlan_network(self, name, vlan_id):
        physical_network = app_settings.COMPLEX_MISC.get("vlan_physical_network") \
                           or "vlanprovider"
        params = {'name': name or "Vlan{}".format(vlan_id),
                  'admin_state_up': "True",
                  'shared': True,
                  'router:external': False,
                  'provider:network_type': "vlan",
                  'provider:physical_network': physical_network,
                  'provider:segmentation_id': vlan_id}
        return self.create_network(**params)
