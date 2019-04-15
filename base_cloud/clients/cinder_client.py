from __future__ import unicode_literals

import logging

from keystoneauth1.identity import v3
from keystoneauth1 import session
from cinderclient import client

try:
    from base_cloud import app_settings
except Exception:
    pass


LOG = logging.getLogger(__name__)
VERSIONS = '2'


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
        self.cinder_client = client.Client(version=VERSIONS,
                                           session=sess)

    def volume_list(self, **kwargs):
        """
        :param detailed:
        :param search_opts:
        :param marker:
        :param limit:
        :param sort_key:
        :param sort_dir:
        :param sort:
        :return:
        """
        return self.cinder_client.volumes.list(**kwargs)

    def volume_get(self, volume_id):
        return self.cinder_client.volumes.get(volume_id)

    def volume_create(self, size, name=None, description=None, volume_type=None,
                      snapshot_id=None, metadata=None, image_id=None,
                      availability_zone=None, source_volid=None):
        data = {'name': name,
                'description': description,
                'volume_type': volume_type,
                'snapshot_id': snapshot_id,
                'metadata': metadata,
                'imageRef': image_id,
                'availability_zone': availability_zone,
                'source_volid': source_volid}
        return self.cinder_client.volumes.create(size, **data)

    def volume_delete(self, volume_id, cascade=False):
        self.cinder_client.volumes.delete(volume_id, cascade)

    def volume_force_delete(self, volume_id):
        self.cinder_client.volumes.force_delete(volume_id)

    def volume_update(self, volume_id, **kwargs):
        vol_data = {'name': kwargs.get("name"),
                    'description': kwargs.get("description")}
        return self.cinder_client.volumes.update(volume_id, **vol_data)

    def volume_attach(self, volume_id, instance_uuid, mountpoint,
                      mode='rw', host_name=None):
        return self.cinder_client.volumes.attach(volume_id, instance_uuid,
                                                 mountpoint, mode, host_name)

    def volume_detach(self, volume_id, attachment_uuid=None):
        return self.cinder_client.volumes.detach(volume_id, attachment_uuid)

    def volume_extend(self, volume_id, new_size):
        self.cinder_client.volumes.extend(volume_id, new_size)

    def service_list(self):
        return self.cinder_client.services.list()

    def snapshot_list(self, **kwargs):
        return self.cinder_client.volume_snapshots.list(**kwargs)

    def snapshot_delete(self, snap_id, force=True):
        self.cinder_client.volume_snapshots.delete(snap_id, force=force)

    def snapshot_create(self, volume_id, force=False,
                        name=None, description=None, metadata=None):
        return self.cinder_client.volume_snapshots.create(
                        volume_id, force=force, name=name,
                        description=description, metadata=metadata)

    def snapshot_get(self, snap_id):
        return self.cinder_client.volume_snapshots.get(snap_id)


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="L5uCdcjQQuyY9DLs", project_name="admin",
                 user_domain_id="default", project_domain_id="default")
    vv = cli.snapshot_get("a860baee-b572-4826-9508-f36209464331")
