# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

from base.utils.functional import cached_property
from base_cloud.clients.nova_client import Client as NovaClient
from base_cloud.storage.views import StorageAction


class Volume(object):

    def __init__(self, operator=None):
        self.operator = operator or StorageAction()

    @cached_property
    def nova_client(self):
        return NovaClient()

    def get(self, volume_id=None, volume_name=None, snapshot_name=None):
        if volume_id:
            return self.operator.get_volume(volume_id)
        elif volume_name:
            volumes = self.operator.list_volumes(search_opts={'name': volume_name})
            if volumes:
                return volumes[0]
        elif snapshot_name:
            snapshots = self.operator.list_volume_snapshots(search_opts={'name': snapshot_name})
            if snapshots:
                return snapshots[0]
            return None
        raise Exception('invalid params')

    def create(self, name, size, volume_type='', description='', **kwargs):
        volume = self.operator.create_volume(name=name, size=size, volume_type=volume_type,
                                             description=description, **kwargs)
        return volume

    def delete(self, volume_id, raise_exception=False):
        try:
            self.operator.delete_volume(volume_id)
        except Exception as e:
            if raise_exception:
                raise e

    def attach_volume(self, volume_id, instance_id):
        return self.nova_client.instance_volume_attach(volume_id, instance_id)

    def detach_volume(self, instance_id, attach_id):
        self.nova_client.instance_volume_detach(instance_id, attach_id)

    def mount(self, volume_id, mnt_dir):
        if not os.path.exists(mnt_dir):
            os.makedirs(mnt_dir)
        subprocess.call('guestmount -a /mnt/cinder/volume-{volume_id} -m /dev/sda1 --ro {mnt_dir}'.format(
            volume_id=volume_id, mnt_dir=mnt_dir), shell=True)

    def umount(self, mnt_dir, remove_dir=False):
        subprocess.call('umount {mnt_dir}'.format(mnt_dir=mnt_dir), shell=True)
        if remove_dir:
            try:
                shutil.rmtree(mnt_dir)
            except OSError:
                pass
