from __future__ import unicode_literals

import copy
import functools
import hashlib
import logging
import math
import memcache
import os
from retry import retry
import six
import time
import urlparse
import uuid

from django.utils.translation import ugettext as _


from base.utils.functional import cached_property
from base_cloud.clients import docker_client
from base_cloud.compute.views import InstanceAction
from base_cloud.docker.views import ContainerAction
from base_cloud.image.views import ImageAction
from base_cloud.network.views import NetworkAction
from base_cloud.storage.views import StorageAction

from base_cloud.exception import FriendlyException
from base_cloud import app_settings
from base_cloud import utils as project_utils
from base_cloud.compute import params as cpt_params
from base_cloud.docker import params as ctn_params
from base_cloud.utils import LazyLoader


LOG = logging.getLogger(__name__)
ATTEMPTS = 900
WINDOWS = "windows"
LINUX = "linux"
ROLE_OPERATOR = "operator"
FLOATING_ROLE = [ROLE_OPERATOR, 'target']
EXTERNAL_NET = "external"
SNAPAHOT_PREFIX = "snapshot"
RESOURCE_TYPES = ['network', 'server', 'container', 'router', 'subnet', 'firewall']
DEFAULT_COMMAND = "sleep infinity;"
states = {
  'ERROR': 'Error', 'RUNNING': 'Running', 'STOPPED': 'Stopped',
  'PAUSED': 'Paused', 'UNKNOWN': 'Unknown', 'CREATING': 'Creating',
  'CREATED': 'Created', 'DELETED': 'Deleted'
}


USED_CIDR_KEY = "used_cidrs"
ALL_CIDR_KEY = "all_cidrs"
AVAILABLE_CIDR_KEY = "available_cidrs"
AVAILABLE_FIPS_KEY = "avialable_fips"
PREALLOCATED_FIPS_KEY = "preallocated_fips"
HYPERVISOR_KEY = "openstack_hypervisors"
PREALLOCATED_RESOURCES = "preallocated_resources"
MEMCACHE_LOCKER_KEY = "memcache_locker"
IMAGES_CACHE_KEY = "glance_all_images"
FLAVORS_CACHE_KEY = "nova_all_flavors"
IMAGE_FOLDER = project_utils.glance_image_dir() or \
               app_settings.COMPLEX_MISC.get("glance_image_dir")
CPU_RATIO = float(project_utils.get_nova_config("DEFAULT", "cpu_allocation_ratio") or
                  app_settings.COMPLEX_MISC.get("cpu_allocation_ratio") or 4.0)
RAM_RATIO = float(project_utils.get_nova_config("DEFAULT", "ram_allocation_ratio") or
                  app_settings.COMPLEX_MISC.get("ram_allocation_ratio") or 1.5)
DISK_RATIO = float(project_utils.get_nova_config("DEFAULT", "disk_allocation_ratio") or
                   app_settings.COMPLEX_MISC.get("disk_allocation_ratio") or 2.0)


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


def check_kwargs(*keys):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            func_name = func.__name__
            LOG.debug("{}(): Check '{}' in kwargs ={}".format(func_name,
                                                              keys, kwargs))
            for key in keys:
                if key not in kwargs:
                    err_msg = "{}(): '{}' not in kwargs " \
                              "{}".format(func_name, key, kwargs.keys())
                    raise FriendlyException(err_msg)
            LOG.debug("{}(): Check success.".format(func_name))
            return func(self, *args, **kwargs)
        return wrapped
    return wrapper


class BaseScene(ImageAction, NetworkAction, InstanceAction, ContainerAction, StorageAction):
    def __init__(self):
        super(BaseScene, self).__init__()
        self.docker_cli = LazyLoader(docker_client.Client,
                                     base_url="tcp://controller:2375")

    @cached_property
    def mc(self):
        return memcache.Client(app_settings.COMPLEX_MISC.get("memcache_host"))

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        raise FriendlyException(err_msg)

    def update_image_cache(self, imgs=None):
        if not imgs:
            imgs = self.list_image()

        img_dict = {}
        for img in imgs:
            img_dict.update({img.name: img.id})
        LOG.debug("update image cache: {}".format(img_dict))
        self.mc.set(IMAGES_CACHE_KEY, img_dict, 86400)
        return img_dict

    def _get_image_from_cache(self, image_name):
        # get image from memcache
        imgs = self.mc.get(IMAGES_CACHE_KEY)
        if imgs and imgs.get(image_name):
            img = self.get_image(id=imgs.get(image_name))
            if img and img.status.lower() == "active":
                return img

        # get image from openstack
        imgs = self.list_image()
        imgs = self.update_image_cache(imgs)
        if imgs and imgs.get(image_name):
            img = self.get_image(id=imgs.get(image_name))
            if img and img.status.lower() == "active":
                return img

        return None

    def _get_image(self, image_name, snapshot=None):
        if snapshot:
            LOG.info('snapshot name: {}'.format(snapshot))
            # image_obj = self.glance_cli.image_get_by_name(snapshot)
            image_obj = self._get_image_from_cache(snapshot)
            if image_obj and image_obj.status.lower() == "active":
                return True, image_obj
            LOG.debug("Snapshot {} status not active, "
                      "Use image {} instead.".format(snapshot, image_name))

        # image_obj = self.get_image(name=image_name)
        image_obj = self._get_image_from_cache(image_name)
        if not image_obj:
            err_msg = _("Image {} not found.").format(image_name)
            self._handle_error(err_msg)
        if image_obj.status.lower() != "active":
            err_msg = _("Image {} status not active.").format(image_name)
            self._handle_error(err_msg)
        return False, image_obj

    @logger_decorator
    def scene_check_docker_image(self, image_name):
        try:
            image = self.docker_cli.inspect_image(image_name)
            if image:
                return True
        except Exception:
            return self.load_docker_image(image_name)

    @logger_decorator
    def load_docker_image(self, image):
        if not IMAGE_FOLDER:
            err_msg = _("Image store data directory not "
                        "configured or not exists.")
            self._handle_error(err_msg)

        if hasattr(image, "id"):
            image_id = image.id
            image_name = image.name
        elif project_utils.is_uuid_like(image):
            image_id = image
            image_name = self.get_image(id=image_id).name
        else:
            image_obj = self._get_image_from_cache(image)
            if image_obj:
                image_id = image_obj.id
                image_name = image
            else:
                return False
        image_path = os.path.join(IMAGE_FOLDER, image_id)

        try:
            img = self.docker_cli.load_image(image_path)
            LOG.info("Loaded docker image {}".format(image_name))
            return img
        except Exception as e:
            err_msg = _("Unable to load docker image {}".format(image_id))
            self._handle_error(err_msg, e)
        return False

    def update_flavor_cache(self, flavors=None):
        if not flavors:
            flavors = self.list_flavor()

        flavor_dict = {}
        for flv in flavors:
            flavor_dict.update({flv.name: flv.id})
        LOG.debug("update flavor cache: {}".format(flavor_dict))
        self.mc.set(FLAVORS_CACHE_KEY, flavor_dict)

    def _get_flavor_from_cache(self, flavor_name):
        # get image from memcache
        flavors = self.mc.get(FLAVORS_CACHE_KEY)
        if flavors and flavors.get(flavor_name):
            flavor = self.get_flavor(flavor_id=flavors.get(flavor_name))
            if flavor:
                return flavor

        # get flavors from openstack
        flavors = self.list_flavor()
        self.update_flavor_cache(flavors)

        for flavor in flavors:
            if flavor.name == flavor_name:
                return flavor
        return None

    def _get_flavor(self, flavor_name=None, os_type=None):
        flavor = None
        if flavor_name:
            flavor = self._get_flavor_from_cache(flavor_name=flavor_name)

        if not flavor:
            LOG.info("Flavor not found, use default flavor.")
            if os_type and os_type == "windows":
                flavor = self._get_flavor_from_cache(
                    flavor_name=app_settings.COMPLEX_MISC.get("windows_flavor"))
            else:
                flavor = self._get_flavor_from_cache(
                    flavor_name=app_settings.COMPLEX_MISC.get("linux_flavor"))
        return flavor

    def _get_default_dns(self):
        return app_settings.COMPLEX_MISC.get("dns_nameservers")

    def _get_security_groups(self):
        return app_settings.COMPLEX_MISC.get("security_groups")

    def _get_keypairs(self, keyname=None):
        return keyname

    def _get_available_zone(self, zone=None):
        return zone

    def _need_floating_ip(self, role=None):
        if role in FLOATING_ROLE:
            return True
        return False

    def _is_compute_target(self, port):
        if port['device_owner'].startswith('compute:') and \
                not port['device_owner'].startswith('compute:kuryr'):
            return True
        return False

    def _is_docker_target(self, port):
        if port['device_owner'].startswith('compute:kuryr'):
            return True
        return False

    def get_scene_router_ifs(self, net_ids):
        router_ifs = []
        for net_id in net_ids:
            router_ifs.extend(self.get_router_ifs(net_id))
        return router_ifs

    @logger_decorator
    def fresh_memcache_fips(self):
        avail_fips = self.load_available_fips_dict()
        self.mc.set(AVAILABLE_FIPS_KEY, avail_fips)
        return avail_fips

    def mark_used_fips(self, pre_fips):
        used_fips = self.mc.get(PREALLOCATED_FIPS_KEY) or {}
        self.mc.set(PREALLOCATED_FIPS_KEY, dict(used_fips, **pre_fips))

    def clean_used_fips(self, pre_fips):
        used_fips = self.mc.get(PREALLOCATED_FIPS_KEY) or {}
        for fip_addr in used_fips.keys():
            if fip_addr in pre_fips.keys():
                used_fips.pop(fip_addr)
        self.mc.set(PREALLOCATED_FIPS_KEY, used_fips)

    def _get_fip(self, skip_cache=False):
        if not skip_cache:
            # get from memcache
            avail_fips = self.mc.get(AVAILABLE_FIPS_KEY) or {}
            pre_fips = self.mc.get(PREALLOCATED_FIPS_KEY) or {}
            for fip_addr in avail_fips.keys():
                if fip_addr in pre_fips.keys():
                    avail_fips.pop(fip_addr)
            if avail_fips:
                fip = avail_fips.popitem()
                self.mc.set(AVAILABLE_FIPS_KEY, avail_fips)
                LOG.debug("Get floating ip {} from memcache".format(fip))
                return fip

            # get from openstack
            avail_fips = self.fresh_memcache_fips()
            if avail_fips:
                for fip_addr in avail_fips.keys():
                    if fip_addr in pre_fips.keys():
                        avail_fips.pop(fip_addr)
                if avail_fips:
                    fip = avail_fips.popitem()
                    self.mc.set(AVAILABLE_FIPS_KEY, avail_fips)
                    LOG.debug("Get floating ip {} from openstack".format(fip))
                    return fip

        # create a new one
        fip = self.create_fip()
        if fip:
            LOG.debug("Create a new floating ip {}".format(fip))
            return (fip.get("floating_ip_address"), fip.get("id"))

        err_msg = _("Unable to get floating ip.")
        self._handle_error(err_msg)

    @retry(tries=3, delay=1)
    @logger_decorator
    def preallocate_fips(self, count):
        pre_fips = {}
        if isinstance(count, list):
            fips_in_os = self.list_floating_ip()
            tmp_fips_dict = {}
            for tmp_fip in fips_in_os:
                if tmp_fip.get("status") == "DOWN" or \
                        tmp_fip.get("fixed_ip_address"):
                    tmp_fips_dict.update(
                        {tmp_fip.get("floating_ip_address"): tmp_fip})

            for ip in count:
                fip = tmp_fips_dict.get(ip)
                if not fip:
                    fip = self.create_fip(ip)
                pre_fips.update({ip: fip.get("id")})
            return pre_fips

        with project_utils.memcache_lock(self.mc, MEMCACHE_LOCKER_KEY):
            # avialable_fips = self.load_available_fips_dict()
            # self.mc.set(AVAILABLE_FIPS_KEY, avialable_fips)
            #
            # for i in range(count):
            #     fip_addr, fip_id = self._get_fip()
            #     pre_fips.update({fip_addr: fip_id})
            #     self.mark_used_fips({fip_addr: fip_id})
            # LOG.debug("Allocated fips : {}".format(pre_fips))
            # self.mark_used_fips(pre_fips)
            for i in range(count):
                fip_addr, fip_id = self._get_fip(skip_cache=True)
                pre_fips.update({fip_addr: fip_id})
        return pre_fips

    def preallocate_ports(self, network_id, count):
        ports = []
        params = {
            "port_security_enabled": False,
            "admin_state_up": True
        }
        if self._get_security_groups():
            params.update({"port_security_enabled": True})

        if isinstance(count, list):
            for ip in count:
                params.update({"fixed_ips": [{"ip_address": ip}]})
                port = self.create_port(network_id, **params)
                ports.append(port)
        else:
            for i in range(count):
                port = self.create_port(network_id, **params)
                ports.append(port)
        return ports

    def _calculate_require(self, servers):
        req_vcpus = 0
        req_memory_size = 0
        req_disk_size = 0
        req_fips = 0

        for vm in servers:
            if vm.get("role") in FLOATING_ROLE:
                req_fips += 1
            os_type = vm.get("system_type")
            flavor = self._get_flavor(vm.get("flavor"), os_type)
            req_vcpus += flavor.vcpus
            req_memory_size += flavor.ram
            disk_size = flavor.disk
            if not disk_size:
                image = self._get_image(image_name=vm.get("image"))
                disk_size = getattr(image, "min_disk", 0)
            req_disk_size += disk_size
        return req_vcpus, req_memory_size, req_disk_size, req_fips

    def _calculate_allowance(self):
        allow_vcpus = 0
        allow_memory_size = 0
        allow_disk_size = 0
        allow_fips = 0

        try:
            hypervisors = self.nova_cli.hypervisor_list()
        except Exception as e:
            err_msg = _("Unable to retire hypervisors.")
            self._handle_error(err_msg, e)

        for hyperv in hypervisors:
            if hyperv.state == "up" and hyperv.status == "enabled":
                hostname = hyperv.hypervisor_hostname

                allow_vcpus += (hyperv.vcpus * CPU_RATIO - hyperv.vcpus_used)
                allow_memory_size += (hyperv.memory_mb * RAM_RATIO - hyperv.memory_mb_used)
                free_disk_gb = hyperv.local_gb * DISK_RATIO - hyperv.local_gb_used
                if hasattr(hyperv, "nova_free_disk_gb"):
                    free_disk_gb = min(free_disk_gb, hyperv.nova_free_disk_gb * DISK_RATIO)
                else:
                    if hostname == project_utils.get_local_hostname():
                        st = os.statvfs(project_utils.nova_instance_dir() or "/")
                        local_free_disk_gb = (st.f_bavail * st.f_frsize)/1024/1024/1024 * DISK_RATIO
                        free_disk_gb = min(free_disk_gb, local_free_disk_gb)
                allow_disk_size += free_disk_gb

        ext_nets = self.mc.get("_check_ext_networks_")
        if not ext_nets:
            try:
                ext_nets = self.neutron_cli.ext_networks_list()
                self.mc.set("_check_ext_networks_", ext_nets, 86400)
            except Exception as e:
                err_msg = _("Unable to retire external networks.")
                self._handle_error(err_msg, e)
        for ext_net in ext_nets:
            net_availability = self.neutron_cli.show_network_ip_availability(ext_net.get("id"))
            allow_fips += (net_availability.get("total_ips", 0) -
                           net_availability.get("used_ips", 0))

        # fips = self.neutron_cli.floating_ip_list()
        # for fip in fips:
        #     if not fip.get("instance_id") or not fip.get("device_id"):
        #         allow_fips += 1
        return allow_vcpus, allow_memory_size, allow_disk_size, allow_fips

    def _calculate_preallocated(self):
        pre_vcpus = 0
        pre_memory_size = 0
        pre_disk_size = 0
        pre_fips = 0

        preallocated_resoureces = self.mc.get(PREALLOCATED_RESOURCES)
        if preallocated_resoureces:
            for _tmp, data in preallocated_resoureces.items():
                pre_vcpus += data.get("vcpus")
                pre_memory_size += data.get("memory_size")
                pre_disk_size += data.get("disk_size")
                pre_fips += data.get("fips")
        return pre_vcpus, pre_memory_size, pre_disk_size, pre_fips

    @logger_decorator
    def ensure_preallocated(self, locker_id, req_vcpus,
                            req_memory_size, req_disk_size, req_fips):
        preallocated_resoureces = self.mc.get(PREALLOCATED_RESOURCES) or {}
        preallocated_resoureces.update({
            locker_id: {
                "vcpus": req_vcpus,
                "memory_size": req_memory_size,
                "disk_size": req_disk_size,
                "fips": req_fips
            }
        })
        self.mc.set(PREALLOCATED_RESOURCES, preallocated_resoureces, 3600)
        LOG.info("Preallocated resource ({}) : ok".format(locker_id))

    @logger_decorator
    def release_preallocated(self, locker_id):
        preallocated_resoureces = self.mc.get(PREALLOCATED_RESOURCES)
        preallocated_resoureces.pop(locker_id)
        self.mc.set(PREALLOCATED_RESOURCES, preallocated_resoureces, 3600)
        LOG.info("Release preallocated resource ({}) : ok".format(locker_id))

    @logger_decorator
    @check_kwargs("servers")
    def scene_allowance_check(self, **kwargs):
        servers = kwargs.get("servers", [])
        locker_id = kwargs.get("locker_id", uuid.uuid4().hex)

        # calc current scene requirements
        req_vcpus, req_memory_size, req_disk_size, req_fips = self._calculate_require(servers)

        # lock memcache and calc remains
        with project_utils.memcache_lock(self.mc, MEMCACHE_LOCKER_KEY):
            LOG.info("Checking hypervisor resources...")
            # calc allowance
            allow_vcpus, allow_memory_size, allow_disk_size, allow_fips = self._calculate_allowance()
            pre_vcpus, pre_memory_size, pre_disk_size, pre_fips = self._calculate_preallocated()

            if allow_fips - pre_fips >= req_fips:
                LOG.debug("Check floating ip quota: OK .")
            else:
                err_msg = _("Check floating ip quota: Error . Required ({}) > "
                            "Allowance ({})) - Preallocated ({})").format(
                            req_fips, allow_fips, pre_fips)
                self._handle_error(err_msg)

            if allow_vcpus - pre_vcpus >= req_vcpus:
                LOG.debug("Check vcpu allowance: OK")
            else:
                err_msg = _("Check vcpu allowance: Error . Required ({}) > "
                            "Allowance ({})) - Preallocated ({})").format(
                            req_vcpus, allow_vcpus, pre_vcpus)
                self._handle_error(err_msg)

            if allow_memory_size - pre_memory_size >= req_memory_size:
                LOG.debug("Check memory allowance: OK")
            else:
                err_msg = _("Check memory allowance: Error . Required ({}) > "
                            "Allowance ({})) - Preallocated ({})").format(
                            req_memory_size, allow_memory_size, pre_memory_size)
                self._handle_error(err_msg)

            if allow_disk_size - pre_disk_size >= req_disk_size:
                LOG.debug("Check disk allowance: OK")
            else:
                err_msg = _("Check disk allowance: Error . Required ({}) > "
                            "Allowance ({})) - Preallocated ({})").format(
                            req_disk_size, allow_disk_size, pre_disk_size)
                self._handle_error(err_msg)

            LOG.info("Check hypervisor resources: Success")
            self.ensure_preallocated(locker_id, req_vcpus,
                                     req_memory_size,
                                     req_disk_size, req_fips)
            return locker_id

    @logger_decorator
    def scene_create_network(self, **kwargs):
        net_name = kwargs['name']
        net_params = {
            'name': net_name,
            'admin_state_up': 'True',
            'shared': kwargs.get('shared', False)
        }
        net = self.create_network(**net_params)

        subnet = None
        cidr = kwargs.get("cidr")
        if cidr:
            subnet_params = {
                'name': "{}_subnet".format(net_name),
                'cidr': cidr,
                'enable_dhcp': kwargs.get("enable_dhcp", True),
                'dns_nameservers': kwargs.get("dns_nameservers"),
                'allocation_pools': [dict(zip(['start', 'end'], pool.strip().split(',')))
                                     for pool in kwargs.get('allocation_pools', "").split('\n')
                                     if pool.strip()]
            }
            if kwargs.get("no_gateway"):
                gateway_ip = None
            else:
                gateway_ip = kwargs.get("gateway_ip")
            subnet_params.update({"gateway_ip": gateway_ip})
            subnet = self.create_subnet(net.get("id"), **subnet_params)
        return net, subnet

    @logger_decorator
    def scene_create_router(self, **kwargs):
        router_params = {
            'name': kwargs.get("name")
        }
        router = self.create_router(**router_params)

        subnet_ids = kwargs.get("subnet_ids")
        if subnet_ids:
            for subnet_id in subnet_ids:
                self.router_bind_subnet(router.get("id"), subnet_id)

        external_net_id = kwargs.get("external_net_id")
        if external_net_id:
            self.router_bind_gateway(router.get("id"),
                                     external_net_id)
        return router

    @logger_decorator
    def get_ports(self, network_id=None, device_id=None):
        params = {}
        if network_id:
            params.update({"network_id": network_id})
        if device_id:
            params.update({"device_id": device_id})

        try:
            return self.neutron_cli.port_list(**params)
        except Exception as e:
            err_msg = _("Unable to get ports for network "
                        "{}.").format(network_id)
            self._handle_error(err_msg, e)

    def _is_router_if_target(self, port):
        if port['device_owner'].startswith('network:router_interface'):
            return True
        return False

    @logger_decorator
    def get_router_ifs(self, network_id=None, device_id=None):
        ports = self.get_ports(network_id=network_id, device_id=device_id)
        return [p.get("id") for p in ports if self._is_router_if_target(p)]

    @logger_decorator
    def scene_create_firewall(self, **kwargs):
        fw_name = kwargs.get("name")

        ingress_rules_list = []
        egress_rules_list = []

        rules = kwargs.get("rule") or []
        for idx, rule in enumerate(rules):
            direction = rule.get("direction")
            rule_name = "{}-rule-{}".format(fw_name, idx)
            rule = {
                "protocol": rule.get("protocol"),
                "action": rule.get("action"),
                "source_ip_address": rule.get("sourceIP") or None,
                "source_port": rule.get("sourcePort") or None,
                "destination_ip_address": rule.get("destIP") or None,
                "destination_port": rule.get("destPort") or None
            }
            if rule.get("protocol") == 'any':
                del rule['protocol']

            if direction == "ingress":
                rule.update({"name": "{}-ingress".format(rule_name)})
                ingress_rules_list.append(rule)
            elif direction == "egress":
                rule.update({"name": "{}-egress".format(rule_name)})
                egress_rules_list.append(rule)
            else:
                rule.update({"name": "{}-ingress".format(rule_name)})
                ingress_rules_list.append(rule)
                rule.update({"name": "{}-egress".format(rule_name)})
                egress_rules_list.append(rule)

        ingress_policy_dict = {"name": "{}-policy-ingress".format(fw_name)}
        egress_policy_dict = {"name": "{}-policy-egress".format(fw_name)}
        firewall_dict = {"name": fw_name}

        LOG.debug("Create firewall rules for {}".format(fw_name))
        ingress_rules = self.create_firewall_rules(ingress_rules_list)
        if ingress_rules:
            ingress_policy_dict.update({"firewall_rules": [r.get("id") for r in ingress_rules]})
        ingress_policy = self.create_firewall_policy(**ingress_policy_dict)
        firewall_dict.update({"ingress_firewall_policy_id": ingress_policy.get("id")})

        egress_rules = self.create_firewall_rules(egress_rules_list)
        if egress_rules:
            egress_policy_dict.update({"firewall_rules": [r.get("id") for r in egress_rules]})
        egress_policy = self.create_firewall_policy(**egress_policy_dict)
        firewall_dict.update({"egress_firewall_policy_id": egress_policy.get("id")})

        ports = kwargs.get("ports")
        if ports:
            firewall_dict.update({"ports": ports})

        LOG.debug("Create firewall {}".format(fw_name))
        return self.create_firewall(**firewall_dict), ingress_rules, egress_rules

    def format_rule_dict(self, rule):
        return {u'protocol': rule.get("protocol"),
                u'source_ip_address': rule.get("sourceIP"),
                u'destination_ip_address': rule.get("destIP"),
                u'action': rule.get("action"),
                u'source_port': rule.get("sourcePort") or None,
                u'destination_port': rule.get("destPort") or None, }

    @logger_decorator
    def scene_delete_firewall_rules(self, firewall_id, **kwargs):
        """
        :param firewall_id:
        :param direction: ingress/egress/both/None
        :param rules: rule ids
        :return:
        """
        firewall = self.get_firewall(firewall_id)
        direction = kwargs.get("direction")
        rules = kwargs.get("rules")
        if not rules:
            rules = [self.format_rule_dict(kwargs)]

        if direction in ['ingress', 'egress']:
            policy = firewall.get("{}_policy".format(direction))
            for rule in rules:
                if isinstance(rule, six.string_types):
                    self.remove_firewall_policy_rule(
                        policy.get("id"), firewall_rule_id=rule)
                    self.check_firewall_status(firewall_id)
                    self.delete_firewall_rule(rule)
                else:
                    rule = self.get_firewall_rule_by_params(policy, rule)
                    if rule:
                        self.remove_firewall_policy_rule(
                            policy.get("id"), firewall_rule_id=rule.get("id"))
                        self.check_firewall_status(firewall_id)
                        self.delete_firewall_rule(rule.get("id"))
        else:
            ingress_policy = firewall.get("ingress_policy")
            egress_policy = firewall.get("egress_policy")
            for orig_rule in rules:
                if isinstance(orig_rule, six.string_types):
                    if orig_rule in ingress_policy.get("firewall_rules"):
                        self.remove_firewall_policy_rule(ingress_policy.get("id"),
                                                         firewall_rule_id=orig_rule)
                        self.check_firewall_status(firewall_id)
                        self.delete_firewall_rule(orig_rule)
                    elif orig_rule in egress_policy.get("firewall_rules"):
                        self.remove_firewall_policy_rule(egress_policy.get("id"),
                                                         firewall_rule_id=orig_rule)
                        self.check_firewall_status(firewall_id)
                        self.delete_firewall_rule(orig_rule)
                else:
                    in_rule_id = self.get_firewall_rule_by_params(
                                                ingress_policy, orig_rule).get("id")
                    if in_rule_id:
                        self.remove_firewall_policy_rule(
                            ingress_policy.get("id"), firewall_rule_id=in_rule_id)
                        self.check_firewall_status(firewall_id)
                    e_rule_id = self.get_firewall_rule_by_params(
                                                egress_policy, orig_rule).get("id")
                    if e_rule_id:
                        self.remove_firewall_policy_rule(
                            egress_policy.get("id"), firewall_rule_id=e_rule_id)
                        self.check_firewall_status(firewall_id)

                    if in_rule_id:
                        self.delete_firewall_rule(in_rule_id)
                        self.check_firewall_status(firewall_id)
                    if e_rule_id and e_rule_id != in_rule_id:
                        self.delete_firewall_rule(e_rule_id)
                        self.check_firewall_status(firewall_id)

        LOG.debug("Deleted rules for firewall {}".format(firewall_id))

    @logger_decorator
    def scene_add_firewall_rules(self, firewall_id, rules):
        firewall = self.get_firewall(firewall_id=firewall_id)
        fw_name = firewall.get("name")
        ingress_rules_list = []
        egress_rules_list = []

        for idx, rule in enumerate(rules):
            direction = rule.get("direction")
            rule_name = "{}-rule-{}".format(fw_name, idx)
            rule = {
                "protocol": rule.get("protocol"),
                "action": rule.get("action"),
                "source_ip_address": rule.get("sourceIP") or None,
                "source_port": rule.get("sourcePort") or None,
                "destination_ip_address": rule.get("destIP") or None,
                "destination_port": rule.get("destPort") or None
            }
            if rule.get("protocol") == 'any':
                del rule['protocol']
            if direction == "ingress":
                rule.update({"name": "{}-ingress".format(rule_name)})
                ingress_rules_list.append(rule)
            elif direction == "egress":
                rule.update({"name": "{}-egress".format(rule_name)})
                egress_rules_list.append(rule)
            else:
                rule.update({"name": "{}-ingress".format(rule_name)})
                ingress_rules_list.append(copy.deepcopy(rule))
                rule.update({"name": "{}-egress".format(rule_name)})
                egress_rules_list.append(copy.deepcopy(rule))

        ingress_policy_dict = {"name": "{}-policy-ingress".format(fw_name)}
        egress_policy_dict = {"name": "{}-policy-egress".format(fw_name)}
        firewall_dict = {}

        ingress_rules = self.create_firewall_rules(ingress_rules_list)
        if ingress_rules:
            ingress_policy = firewall.get("ingress_policy")
            if ingress_policy:
                for rule in ingress_rules:
                    self.check_firewall_status(firewall_id)
                    self.insert_firewall_policy_rule(ingress_policy.get("id"),
                                                     firewall_rule_id=rule.get("id"))
            else:
                ingress_policy_dict.update({"firewall_rules": [r.get("id") for r in ingress_rules]})
                ingress_policy = self.create_firewall_policy(**ingress_policy_dict)
                firewall_dict.update({"ingress_firewall_policy_id": ingress_policy.get("id")})

        egress_rules = self.create_firewall_rules(egress_rules_list)
        if egress_rules:
            egress_policy = firewall.get("egress_policy")
            if egress_policy:
                for rule in egress_rules:
                    self.check_firewall_status(firewall_id)
                    self.insert_firewall_policy_rule(egress_policy.get("id"),
                                                     firewall_rule_id=rule.get("id"))
            else:
                egress_policy_dict.update({"firewall_rules": [r.get("id") for r in egress_rules]})
                egress_policy = self.create_firewall_policy(**egress_policy_dict)
                firewall_dict.update({"egress_firewall_policy_id": egress_policy.get("id")})

        if firewall_dict:
            self.update_firewall(firewall_id, **firewall_dict)

        return ingress_rules, egress_rules

    @logger_decorator
    def scene_get_port(self, network_id=None,
                       instance=None, container=None):
        if container:
            LOG.debug("Get port for container "
                      "{}".format(network_id, container.name))
            addrs = container.addresses
            port_ids = []
            for net_id, ports in addrs.items():
                for port in ports:
                    if port.get("port"):
                        port.update({"id": port.get("port")})
                        port_ids.append(port)
            if port_ids:
                return port_ids[0]

        if instance:
            LOG.debug("Get port for network {}, instance "
                      "{}".format(network_id, instance.name))
            ports = self.get_ports(network_id=network_id,
                                   device_id=instance.id)
            if ports:
                return ports[0]

    @logger_decorator
    def scene_create_qos(self, **kwargs):
        policy_name = kwargs.get("name")
        policy = self.create_qos_policy(name=policy_name)
        LOG.info("Qos policy {} created".format(policy_name))

        rule = kwargs.get("rule")
        if rule:
            qos_ingress_limit = rule.get("ingress")
            if qos_ingress_limit:
                self.create_qos_bandwidth_limit_rule(policy.get("id"), **{
                    "direction": "ingress",
                    "max_kbps": qos_ingress_limit,
                    "max_burst_kbps": qos_ingress_limit
                })
            qos_egress_limit = rule.get("egress")
            if qos_egress_limit:
                self.create_qos_bandwidth_limit_rule(policy.get("id"), **{
                    "direction": "egress",
                    "max_kbps": qos_egress_limit,
                    "max_burst_kbps": qos_egress_limit
                })
            LOG.info("Qos policy rule created "
                     "for policy {}".format(policy_name))

        instance = kwargs.get("instance")
        container = kwargs.get("container")
        network_id = kwargs.get("network_id")
        if network_id and (instance or container):
            port = self.scene_get_port(network_id, instance, container)
            if port:
                self.bind_port_qos_policy(port.get("id"), policy.get("id"))
        return policy

    def _get_server_userdata(self, attach_url, os_type=None,
                             users=None, custom_script=None,
                             install_script=None, init_script=None,
                             from_snapshot=False, report_started=None,
                             report_inited=None):
        if os_type.lower() == WINDOWS:
            userdata = cpt_params.powershell_start

            # status change to started
            if report_started:
                userdata += cpt_params.report_started_status.format(report_started)

            # add user for windows instance
            if users:
                # has_xctf_user = False
                for user in users:
                    username = user.get("username")
                    password = user.get("password") or project_utils.generate_complex_str()
                    if username == "administrator":
                        userdata += cpt_params.windows_change_user_pwd.format(username=username,
                                                                              password=password)
                        continue
                    userdata += cpt_params.windows_user_create.format(username=username)
                    userdata += cpt_params.windows_change_user_pwd.format(username=username,
                                                                          password=password)
                    userdata += cpt_params.windows_add_user_to_rdp.format(username=username)

                    # if username == "xctf":
                    #     has_xctf_user = True
            # else:
            #     # if not has_xctf_user:
            #     # change xctf user password
            #     xctf_pwd = project_utils.generate_complex_str()
            #     userdata += cpt_params.windows_user_create.format(username="xctf")
            #     userdata += cpt_params.windows_change_user_pwd.format(username="xctf", password=xctf_pwd)
            #     userdata += cpt_params.windows_add_user_to_rdp.format(username="xctf")

            if attach_url:
                # download zip file
                zip_file_name = urlparse.urlsplit(attach_url).path.split("/")[-1]
                file_folder = os.path.splitext(zip_file_name)[0]
                userdata += cpt_params.windows_download_zip.format(zip_file_name=zip_file_name,
                                                                   attach_url=attach_url,
                                                                   file_folder=file_folder)

                if install_script:
                    # execute install scripts
                    script_path = install_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += cpt_params.windows_install_evn.format(file_folder=file_folder,
                                                                      script_folder=script_folder,
                                                                      install_script=install_script)
                if init_script:
                    script_path = init_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += cpt_params.windows_init_services.format(file_folder=file_folder,
                                                                        script_folder=script_folder,
                                                                        init_script=init_script)

                # delete zip file if not debug
                if app_settings.COMPLEX_MISC.get("clean_env", False):
                    userdata += cpt_params.windows_clean_env.format(file_folder=file_folder)

            # status change to running
            if report_inited:
                userdata += cpt_params.report_inited_status.format(report_inited)

            if custom_script:
                userdata += custom_script
                userdata += '\r\n'

            return userdata
        elif os_type.lower() == LINUX:
            userdata = cpt_params.user_data_start

            # pop root user
            for idx, user in enumerate(users):
                if user.get("username") == "root":
                    root_pwd = users.pop(idx).get("password", "").strip()
                    if not root_pwd:
                        root_pwd = project_utils.generate_complex_str(length=12)
                    userdata += cpt_params.change_root_pwd.format(root_pwd=root_pwd)
                    break

            # create users
            if users:
                groups = []
                userdata += cpt_params.add_group_prefix
                userdata += cpt_params.add_user_prefix
                for user in users:
                    username = user.get("username")
                    password = user.get("password") or project_utils.generate_complex_str(length=12)
                    sudo = user.get("permission", {}).get("sudo")
                    if username == "root":
                        continue
                    groups.append(cpt_params.add_group.format(group=username))
                    if sudo:
                        userdata += cpt_params.add_user_with_sudo.format(
                                                           group=username,
                                                           username=username,
                                                           password=password)
                    else:
                        userdata += cpt_params.add_user.format(group=username,
                                                               username=username,
                                                               password=password)
                # add groups
                userdata = userdata.format(groups="".join(groups))
            # custom shell script start
            userdata += cpt_params.script_block_start

            # status change to started
            if report_started:
                userdata += cpt_params.report_started_status.format(report_started)

            if attach_url:
                # download zip file
                zip_file_name = urlparse.urlsplit(attach_url).path.split("/")[-1]
                file_folder = os.path.splitext(zip_file_name)[0]
                userdata += cpt_params.download_zip.format(zip_file_name=zip_file_name,
                                                           attach_url=attach_url,
                                                           file_folder=file_folder)
                if install_script and not from_snapshot:
                    # execute install scripts
                    script_path = install_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += cpt_params.install_evn.format(file_folder=file_folder,
                                                              script_folder=script_folder,
                                                              install_script=install_script)
                if init_script:
                    script_path = init_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += cpt_params.init_services.format(file_folder=file_folder,
                                                                script_folder=script_folder,
                                                                init_script=init_script)

                # delete zip file if not debug
                if app_settings.COMPLEX_MISC.get("clean_env", False):
                    userdata += cpt_params.clean_env.format(file_folder=file_folder)
            else:
                if install_script and not from_snapshot:
                    userdata += "\n{}\n".format(install_script)
                if init_script:
                    userdata += "\n{}\n".format(init_script)

            # status change to running
            if report_inited:
                userdata += cpt_params.report_inited_status.format(report_inited)

            if custom_script:
                userdata += custom_script
                userdata += '\n'

            # user data end line
            userdata += cpt_params.user_data_end
            return userdata
        return None

    @logger_decorator
    def scene_create_server(self, **kwargs):
        vm_id = kwargs.get("id")
        name = kwargs.get("name") or vm_id
        attach_url = kwargs.get("attach_url")

        from_snapshot, image = self._get_image(kwargs.get("image"))
        os_type = kwargs.get("system_type") or "linux"
        # role = kwargs.get("role")
        flavor = self._get_flavor(kwargs.get("flavor"), os_type)
        users = kwargs.get("users") or []

        user_data = self._get_server_userdata(attach_url, os_type, users,
                                              custom_script=kwargs.get("custom_script"),
                                              install_script=kwargs.get("install_script"),
                                              init_script=kwargs.get("init_script"),
                                              from_snapshot=False,
                                              report_started=kwargs.get("report_started"),
                                              report_inited=kwargs.get("report_inited"))
        srv_dict = {
            "name": name,
            "image": image,
            "flavor": flavor,
            "key_name": self._get_keypairs(),
            "user_data": user_data,
            "security_groups": kwargs.get("security_groups") or self._get_security_groups(),
            "nics": kwargs.get("nics"),
            "availability_zone": self._get_available_zone()
        }

        server = self.check_server_status(self.create_server(**srv_dict))

        floating_ip = kwargs.get("floating_ip")
        if floating_ip:
            fip_obj = self.bind_fip(floating_ip, instance=server)
            setattr(server, "floating_ip", fip_obj.get("floating_ip_address"))

        return server

    @logger_decorator
    def scene_send_create_server(self, **kwargs):
        vm_id = kwargs.get("id")
        name = kwargs.get("name") or vm_id
        attach_url = kwargs.get("attach_url")

        # from_snapshot = False
        image = kwargs.get("image") or ''
        if image:
            from_snapshot, image = self._get_image(image)

        os_type = kwargs.get("system_type") or "linux"
        # role = kwargs.get("role")
        flavor = self._get_flavor(kwargs.get("flavor"), os_type)
        users = kwargs.get("users") or []

        user_data = self._get_server_userdata(attach_url, os_type, users,
                                              custom_script=kwargs.get("custom_script"),
                                              install_script=kwargs.get("install_script"),
                                              init_script=kwargs.get("init_script"),
                                              from_snapshot=False,
                                              report_started=kwargs.get("report_started"),
                                              report_inited=kwargs.get("report_inited"))
        srv_dict = {
            "name": name,
            "image": image,
            "flavor": flavor,
            "key_name": self._get_keypairs(),
            "user_data": user_data,
            "security_groups": kwargs.get("security_groups") or self._get_security_groups(),
            "nics": kwargs.get("nics"),
            "availability_zone": self._get_available_zone(),
            "block_device_mapping_v2": kwargs.get("block_device_mapping_v2"),
        }

        return self.create_server(**srv_dict)

    @logger_decorator
    def scene_check_create_server(self, server, **kwargs):
        server_obj = self.check_server_status(server)

        floating_ip = kwargs.get("floating_ip")
        if floating_ip:
            fip_obj = self.bind_fip(floating_ip, instance=server_obj)
            setattr(server_obj, "floating_ip", fip_obj.get("floating_ip_address"))

        return server_obj

    def _get_container_userdata(self, attach_url, os_type=None, users=None, run=True,
                                custom_script=None, install_script=None, init_script=None,
                                report_started=None, report_inited=None):
        userdata = []
        if report_started:
            userdata.append(ctn_params.report_started_status.format(report_started))

        if attach_url:
            zip_file_name = urlparse.urlsplit(attach_url).path.split("/")[-1]
            file_folder = os.path.splitext(zip_file_name)[0]

            # download zip file
            userdata.append(ctn_params.download_zip.format(
                zip_file_name=zip_file_name, attach_url=attach_url))

            # unzip zip file
            userdata.append(ctn_params.unzip_file.format(
                zip_file_name=zip_file_name, file_folder=file_folder))

            # execute install.sh
            if install_script:
                script_path = install_script.split()[0]
                script_folder = os.path.join(file_folder,
                                             os.path.split(script_path)[0])
                userdata.append(ctn_params.change_dir.format(script_folder=script_folder))
                userdata.append(ctn_params.install_evn.format(file_folder=file_folder,
                                                              script_folder=script_folder,
                                                              init_script=init_script))

            # execute init.sh
            if init_script:
                script_path = init_script.split()[0]
                script_folder = os.path.join(file_folder,
                                             os.path.split(script_path)[0])
                userdata.append(ctn_params.change_dir.format(script_folder=script_folder))
                userdata.append(ctn_params.init_services.format(file_folder=file_folder,
                                                                script_folder=script_folder,
                                                                init_script=init_script))
        else:
            if install_script:
                userdata.append(install_script)
            if init_script:
                userdata.append(init_script)

        if report_inited:
            userdata.append(ctn_params.report_inited_status.format(report_inited))

        if custom_script:
            userdata.append(custom_script)
        # if run:
        #     userdata.append(DEFAULT_COMMAND)

        return userdata

    @logger_decorator
    # @retry(tries=2, delay=5)
    def scene_create_container(self, **kwargs):
        cont_id = kwargs.get("id")
        name = kwargs.get("name") or cont_id
        attach_url = kwargs.get("attach_url")

        os_type = kwargs.get("system_type") or "linux"
        # flavor = self._get_flavor(kwargs.get("flavor"), os_type)
        users = kwargs.get("users") or []

        run = kwargs.get("run", True)
        command = ""
        if attach_url:
            commands = self._get_container_userdata(
                                     attach_url, os_type, users, run,
                                     custom_script=kwargs.get("custom_script"),
                                     install_script=kwargs.get("install_script"),
                                     init_script=kwargs.get("init_script"),
                                     report_started=kwargs.get("report_started"),
                                     report_inited=kwargs.get("report_inited"))
            if commands:
                command = "/bin/bash -c '{}'".format(' ; '.join(commands))

        params = {
            "name": name,
            "image": self._get_image_from_cache(kwargs.get("image")),
            "image_driver": "glance",
            "nets": kwargs.get("nics"),
            "interactive": True,
            "security_groups": kwargs.get("security_groups") or self._get_security_groups(),
            "command": command,
            "run": run
        }
        # if flavor:
        #     params.update({"cpu": flavor.vcpus, "memory": flavor.ram})

        container = self.check_container_status(self.create_container(**params))
        floating_ip = kwargs.get("floating_ip")
        if floating_ip and container.addresses:
            port = "{}_{}".format(container.addresses.values()[0][0].get('port'),
                                  container.addresses.values()[0][0].get('addr'))
            fip_obj = self.bind_fip(floating_ip, port=port)
            setattr(container, "floating_ip", fip_obj.get("floating_ip_address"))

        return container

    @logger_decorator
    def scene_send_create_container(self, **kwargs):
        cont_id = kwargs.get("id")
        name = kwargs.get("name") or cont_id
        attach_url = kwargs.get("attach_url")

        os_type = kwargs.get("system_type") or "linux"
        # flavor = self._get_flavor(kwargs.get("flavor"), os_type)
        users = kwargs.get("users") or []

        run = kwargs.get("run", True)
        command = ""
        if attach_url:
            commands = self._get_container_userdata(
                attach_url, os_type, users, run,
                custom_script=kwargs.get("custom_script"),
                install_script=kwargs.get("install_script"),
                init_script=kwargs.get("init_script"),
                report_started=kwargs.get("report_started"),
                report_inited=kwargs.get("report_inited"))
            if commands:
                command = "/bin/bash -c '{}'".format(' ; '.join(commands))

        params = {
            "name": name,
            "image": kwargs.get("image"),
            "image_driver": "glance",
            "nets": kwargs.get("nics"),
            "interactive": True,
            "security_groups": kwargs.get("security_groups") or self._get_security_groups(),
            "command": command,
            "run": run
        }
        # if flavor:
        #     params.update({"cpu": flavor.vcpus, "memory": flavor.ram})

        return self.create_container(**params)

    @logger_decorator
    def scene_check_create_container(self, container, **kwargs):
        container_obj = self.check_container_status(container)
        addresses = container_obj.addresses
        for net_id, subnets in addresses.items():
            for idx, subnet in enumerate(subnets):
                port = self.get_port(subnet.get("port"))
                container_obj.addresses[net_id][idx].update({"mac_addr": port.get("mac_address")})
        return container_obj

    @logger_decorator
    def disconnect_ports(self, router_id):
        ports = self.get_ports(device_id=router_id)
        for port in ports:
            try:
                if port['device_owner'] == 'network:router_gateway':
                    self.router_remove_gateway(router_id)
                else:
                    self.router_remove_port(
                        router_id, port_id=port.get("id"))
                LOG.info("Successfully deleted port {} in "
                         "router {}".format(port.get("id"), router_id))
            except Exception as e:
                err_msg = _("Unable to delete "
                            "port {}.").format(port.get("id"))
                LOG.error(err_msg)
                LOG.error(e)

    @logger_decorator
    def scene_delete_router(self, router_id):
        static_routes = self.list_static_routes(router_id)
        if static_routes:
            self.remove_static_route(router_id, static_routes)
        self.disconnect_ports(router_id)
        super(BaseScene, self).delete_router(router_id)

    @logger_decorator
    def scene_delete_qos_policy(self, policy_id):
        try:
            rules = self.list_qos_bandwidth_limit_rules(policy_id)
            for rule in rules:
                self.delete_qos_bandwidth_limit_rule(rule.get("id"), policy_id)
            self.delete_qos_policy(policy_id)
        except Exception as e:
            err_msg = _("Unable to delete qos policy {}.").format(policy_id)
            LOG.error(err_msg)
            LOG.error(e)

    @logger_decorator
    def scene_delete_firewall_policy(self, policy_id):
        try:
            policy = self.get_firewall_policy(policy_id)
            self.neutron_cli.firewall_policy_delete(policy_id)
            while 1:
                try:
                    self.neutron_cli.get_firewall_policy(policy_id)
                    time.sleep(1)
                    continue
                except Exception:
                    LOG.debug("Deleted firewall policy {}".format(policy_id))
                break
        except Exception as e:
            err_msg = _("Unable to delete firewall policy {}.").format(policy_id)
            LOG.error(err_msg)
            LOG.error(e)

        rules = policy.get("firewall_rules") or []
        for rule_id in rules:
            self.delete_firewall_rule(rule_id)

    @logger_decorator
    def scene_delete_firewall(self, firewall_id):
        try:
            firewall = self.update_firewall(firewall_id, ports=[])
            self.check_firewall_status(firewall_id, "INACTIVE")

            self.neutron_cli.firewall_delete(firewall_id)
            while 1:
                try:
                    self.neutron_cli.firewall_get(firewall_id)
                    time.sleep(1)
                    continue
                except Exception:
                    LOG.debug("Deleted firewall {}".format(firewall_id))
                break
        except Exception as e:
            err_msg = _("Unable to delete firewall {}.").format(firewall_id)
            LOG.error(err_msg)
            LOG.error(e)

        ingress_policy = firewall.get("egress_firewall_policy_id")
        egress_policy = firewall.get("ingress_firewall_policy_id")
        if ingress_policy:
            self.scene_delete_firewall_policy(ingress_policy)
        if egress_policy and egress_policy != ingress_policy:
            self.scene_delete_firewall_policy(egress_policy)

    def scene_create_vlan_network(self, name="", vlan_id=None, gateway="",
                                  cidr="", interfaces=None):
        if not name:
            name = "Vlan-{}".format(vlan_id)
        try:
            vlan_net = self.create_vlan_network(name, vlan_id)
            net_id = vlan_net.get("id")
        except Exception as e:
            err_msg = "Unable to create vlan network ({}).".format(vlan_id)
            self._handle_error(err_msg, e)

        try:
            vlan_subnet = self.create_subnet(net_id,
                                             name="{}-subnet".format(name),
                                             cidr=cidr,
                                             gateway_ip=gateway)
        except Exception as e:
            err_msg = "Unable to create vlan subnet ({}).".format(vlan_id)
            try:
                self.delete_network(net_id, sync=False)
            except Exception as e:
                LOG.error(e)
            self._handle_error(err_msg, e)

        try:
            if cidr:
                netmask = cidr.split("/")[-1]
            else:
                netmask = "24"
            s_vlan = self.create_switch_vlan(vlan_id=vlan_id,
                                             gateway=gateway,
                                             netmask=netmask,
                                             interface_id=interfaces)
        except Exception as e:
            err_msg = "Unable to create vlan ({}) in switch".format(vlan_id)
            try:
                self.delete_switch_vlan(vlan_id=vlan_id)
            except Exception as e:
                LOG.error(e)

            try:
                self.delete_network(net_id, sync=False)
            except Exception as e:
                LOG.error(e)
            self._handle_error(err_msg, e)

        return vlan_net, vlan_subnet, s_vlan

    def scene_delete_vlan_network(self, network_id):
        net = self.get_network(network_id)
        if not net:
            return

        subnets = self.get_subnet_by_network_id(net.get("id"))
        for subnet in subnets:
            self.delete_subnet(subnet.get("id"))

        vlan_id = net.get("provider:segmentation_id")
        if vlan_id:
            try:
                self.delete_switch_vlan(vlan_id)
            except Exception:
                err_msg = "Unable to delete switch vlan ({})".format(vlan_id)
                LOG.error(err_msg)
        try:
            self.delete_network(network_id)
        except Exception:
            err_msg = "Unable to delete network ({})".format(network_id)
            LOG.error(err_msg)

    def scene_convert_img_to_disk(self, image_id):
        image = self.check_image_status(image_id)
        if not image:
            err_msg = "Unable to get image by id ({})".format(image_id)
            self._handle_error(err_msg)

        size = int(math.ceil((image.size / 1024.0 / 1024 / 1024) / 10) * 10)
        try:
            volume = self.create_volume(size=size, name=image.name, image_id=image_id)
            self.check_volume_status(volume)
        except Exception as e:
            err_msg = "Unable to create volume " \
                      "from image ({})".format(image.name)
            self._handle_error(err_msg, e)

        try:
            snap = self.create_volume_snapshot(volume_id=volume.id, name=volume.name)
        except Exception as e:
            err_msg = "Unable to create volume snapshot" \
                      "from volume ({})".format(volume.name)
            self._handle_error(err_msg, e)

        return volume, snap

    def scene_delete_img_with_disk(self, image_name):
        volumes = self.list_volumes(search_opts={"name": image_name})
        if not volumes:
            # self._handle_error()
            return

        volume = volumes[0]
        snaps = self.list_volume_snapshots(search_opts={"volume_id": volume.id})
        for snap in snaps:
            try:
                self.delete_volume_snapshot(snap.id, is_async=False)
            except Exception as e:
                err_msg = "Unable to delete snapshot " \
                          "({}) : {}".format(snap.id, e)
                LOG.error(err_msg)

        try:
            self.delete_volume(volume.id)
        except Exception as e:
            err_msg = "Unable to delete volume " \
                      "({}) : {}".format(volume.id, e)
            LOG.error(err_msg)

    def scene_create_docker_network(self, network_id):
        try:
            return self.zun_cli.network_create(network_id)
        except Exception as e:
            err_msg = "Unable to create docker network " \
                      "({})".format(network_id)
            self._handle_error(err_msg, e)

    def scene_delete_docker_network(self, network_id):
        nets = self.docker_cli.list_networks(names=[network_id])
        if not nets:
            LOG.debug("Pass delete docker network {}, Not Found.".format(network_id))
            return

        for net in nets:
            try:
                self.docker_cli.remove_network(net.get("Id"))
            except Exception as e:
                err_msg = "Unable to delete docker network " \
                          "({}), {}".format(network_id, e)
                LOG.error(err_msg)

    def check_first_boot(self, instance_id=None, image=None):
        if instance_id:
            attempts = 60
            while 1:
                if attempts <= 0:
                    err_msg = "Timeout for getting instance ({}) " \
                              "hypervisor hostname".format(instance_id)
                    self._handle_error(err_msg)

                server = self.get_server(instance_id)
                hostname = getattr(server, "OS-EXT-SRV-ATTR:hypervisor_hostname")
                if hostname:
                    LOG.debug("[OPENSTACK] get hypervisor name ({}) "
                              "for server ({})".format(hostname, instance_id))
                    break
                attempts -= 1
                time.sleep(1)

            try:
                return self.nova_cli.check_first_boot(instance_id=instance_id)
            except Exception as e:
                err_msg = "Unable to check first boot."
                self._handle_error(err_msg, e)

        if image:
            if project_utils.get_local_hostname() == "controller":
                inst_path = project_utils.nova_instance_dir()
                if not inst_path:
                    return None

                if project_utils.is_uuid_like(image):
                    image_obj = self.get_image(id=image)
                else:
                    image_obj = self.get_image(name=image)
                if not image_obj:
                    return None
                image_hash = hashlib.sha1(image_obj.id).hexdigest()
                image_cache_path = os.path.join(inst_path, "_base", image_hash)
                if os.path.exists(image_cache_path):
                    LOG.info('Image ({}) first boot.'.format(image_obj.name))
                    return True
                else:
                    return False
        return None
