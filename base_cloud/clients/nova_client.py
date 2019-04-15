from __future__ import unicode_literals

import logging

from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client

try:
    from base_cloud import app_settings
except Exception:
    pass


LOG = logging.getLogger(__name__)
CACHE_KEY = 'nova_all_instances'


class Client(object):
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
        self.nova_client = client.Client("2.1", session=sess)

    def instance_get_all(self, search_opts=None, all_tenants=False):
        if search_opts is None:
            search_opts = {}
        if all_tenants:
            search_opts.update({'all_tenants': True})
        return self.nova_client.servers.list(detailed=True,
                                             search_opts=search_opts)

    def ad_instances_get(self, prefix):
        user_inst = compute_inst = None
        try:
            user_inst = self.nova_client.servers.find(name=prefix+"user")
            compute_inst = self.nova_client.servers.find(name=prefix+"compute")
        except Exception:
            pass
        return user_inst, compute_inst

    def instance_get(self, instance_id=None, instance_name=None, instance_ip=None):
        if instance_id:
            return self.instance_get_by_id(instance_id)
        elif instance_name:
            return self.instance_get_by_name(instance_name)
        elif instance_ip:
            return self.instance_get_by_ip(instance_ip)
        return None

    def instance_get_by_id(self, instance_id):
        return self.nova_client.servers.get(instance_id)

    def instance_get_by_name(self, instance_name):
        search_opts = {'name': instance_name}
        insts = self.instance_get_all(search_opts=search_opts)
        if insts:
            for inst in insts:
                if inst.name == instance_name:
                    return inst
        return None

    def instance_get_by_ip(self, instance_ip):
        insts = self.instance_get_all()
        for inst in insts:
            for net in inst.addresses.values():
                for addr in net:
                    if instance_ip in addr.values():
                        return inst
        return None

    def instance_list_by_name(self, prefix):
        inst_list = []
        insts = self.instance_get_all()
        for inst in insts:
            if inst.name.startswith(prefix):
                inst_list.append(inst)
        return inst_list

    def instance_create(self, name, image, flavor, key_name, user_data,
                        security_groups, block_device_mapping=None,
                        block_device_mapping_v2=None, nics=None,
                        availability_zone=None, instance_count=1, admin_pass=None,
                        disk_config=None, config_drive=True, meta=None,
                        scheduler_hints=None):
        return self.nova_client.servers.create(
                            name, image, flavor, userdata=user_data,
                            security_groups=security_groups,
                            key_name=key_name, block_device_mapping=block_device_mapping,
                            block_device_mapping_v2=block_device_mapping_v2,
                            nics=nics, availability_zone=availability_zone,
                            min_count=instance_count, admin_pass=admin_pass,
                            disk_config=disk_config, config_drive=config_drive,
                            meta=meta, scheduler_hints=scheduler_hints)

    def instance_update(self, instance, name):
        instance_id = instance.id if hasattr(instance, "id") else instance
        self.nova_client.servers.update(instance_id, name=name)

    def instance_delete(self, instance):
        instance_id = instance.id if hasattr(instance, "id") else instance
        self.nova_client.servers.delete(instance_id)

    def flavor_list(self, is_public=True):
        # TODO: add cache
        # flavors = cache.get("cp_all_flavors")
        # if not flavors:
        #     flavors = self.nova_client.flavors.list(is_public=is_public)
        #     cache.set("cp_all_flavors", flavors, 3600)
        # return flavors
        return self.nova_client.flavors.list(is_public=is_public)

    def flavor_get_by_name(self, flavor_name):
        flavors = self.flavor_list()
        for flavor in flavors:
            if flavor.name == flavor_name:
                return flavor
        return None

    def flavor_get(self, flavor_id):
        return self.nova_client.flavors.get(flavor_id)

    def security_group_list(self):
        return self.nova_client.security_groups.list()

    def security_group_get_by_name(self, sg_name):
        groups = self.security_group_list()
        for group in groups:
            if group.name == sg_name:
                return group
        return None

    def instance_stop(self, instance_id):
        self.nova_client.servers.stop(instance_id)

    def instance_start(self, instance_id):
        self.nova_client.servers.start(instance_id)

    def instance_pause(self, instance_id):
        self.nova_client.servers.pause(instance_id)

    def instance_unpause(self, instance_id):
        self.nova_client.servers.unpause(instance_id)

    def instance_reboot(self, instance_id, reboot_type='HARD'):
        self.nova_client.servers.reboot(instance_id, reboot_type)

    def instance_rebuild(self, instance_id, image):
        return self.nova_client.servers.rebuild(instance_id, image)

    def network_update(self, instance_id, nets2add, nets2del):
        for net_id in nets2add:
            self.interface_attach(instance_id, None,
                                  net_id, None)
        for net_id in nets2del:
            self.interface_detach(instance_id, net_id)

    def interface_attach(self, instance_id, port_id=None, net_id=None, fixed_ip=None):
        self.nova_client.servers.interface_attach(instance_id,
                                                  port_id,
                                                  net_id,
                                                  fixed_ip)

    def interface_detach(self, instance_id, port_id):
        self.nova_client.servers.interface_detach(instance_id, port_id)

    def snapshot_create(self, instance_id, name):
        return self.nova_client.servers.create_image(instance_id, name)

    # def floating_ip_list(self):
    #     return self.nova_client.floating_ips.list()
    #
    # def floating_ip_get(self, floating_ip_id):
    #     return self.nova_client.floating_ips.get(floating_ip_id)
    #
    # def floating_ip_get_by_address(self, ip_addr):
    #     fips = self.floating_ip_list()
    #     for fip in fips:
    #         if fip.ip == ip_addr:
    #             return fip
    #     return None
    #
    # def floating_ip_associate(self, fip, inst):
    #     inst = self.instance_get(inst) if hasattr(inst, "id") else inst
    #     fip = self.floating_ip_get(fip) if hasattr(fip, "id") else fip
    #     return self.nova_client.servers.add_floating_ip(inst, fip)
    #
    # def fip_associate_by_addr(self, fip_addr, inst_id):
    #     return self.nova_client.servers.add_floating_ip(inst_id, fip_addr)
    #
    # def floating_ip_disassociate(self, floating_ip_id):
    #     fip = self.floating_ip_get(floating_ip_id)
    #     inst = self.instance_get(fip.instance_id)
    #     return self.nova_client.servers.remove_floating_ip(inst, fip.ip)
    #
    # def fip_disassociate_by_addr(self, fip_addr, inst_id):
    #     return self.nova_client.servers.remove_floating_ip(inst_id, fip_addr)
    #
    # def floating_ip_pools_list(self):
    #     return self.nova_client.floating_ip_pools.list()
    #
    # def floating_ip_allocate(self, pool=None):
    #     return self.nova_client.floating_ips.create(pool)

    def vnc_console(self, inst_id, console_type='novnc'):
        return self.nova_client.servers.get_vnc_console(inst_id, console_type)['console']

    def spice_console(self, inst_id, console_type='spice-html5'):
        return self.nova_client.servers.get_spice_console(inst_id, console_type)['console']

    def hypervisor_list(self):
        return self.nova_client.hypervisors.list()

    def hypervisor_stats(self):
        return self.nova_client.hypervisors.statistics()

    def flavor_create(self, **kwargs):
        return self.nova_client.flavors.create(**kwargs)

    def instance_volume_attach(self, volume_id, instance_id, device=None):
        return self.nova_client.volumes.create_server_volume(instance_id,
                                                             volume_id,
                                                             device)

    def instance_volume_detach(self, instance_id, volume_id):
        return self.nova_client.volumes.delete_server_volume(instance_id,
                                                             volume_id)

    def instance_add_metadata(self, instance, metadata):
        instance_id = instance.id if hasattr(instance, "id") else instance
        self.nova_client.servers.set_meta(instance_id, metadata)

    def instance_delete_metadata(self, instance, keys):
        instance_id = instance.id if hasattr(instance, "id") else instance
        self.nova_client.servers.delete_meta(instance_id, keys)

    def service_list(self):
        return self.nova_client.services.list()

    def password_change(self, instance, password):
        # need to install qemu-guest-agent in guest server & update image metadata
        server_id = instance.id if hasattr(instance, "id") else instance
        self.nova_client.servers.change_password(server_id, password)

    def check_first_boot(self, instance_id):
        return self.nova_client.servers.check_first_boot(instance_id)


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="ADMIN_PASS", project_name="admin",
                 user_domain_id="default", project_domain_id="default")
    flvs = cli.flavor_list()
    isn = cli.instance_get_all(search_opts={"name": "OJ"})
    aaa = cli.instance_get_all(search_opts={"status": "ERROR"})
    dd = cli.change_password("670b6d7d-970c-4170-bb3a-db6da939a1ab", "kkkkyyyy123")
    inst = cli.instance_get_by_id("7aae3171-43b5-49af-aa48-487fbbe1b289")
    vol_id = "d18e3ecf-b631-4a76-81d7-ac1308bda2b1"
    cli.instance_volume_attach(vol_id, inst.id)

    cli.instance_volume_detach(inst.id, vol_id)
