from __future__ import unicode_literals

import logging
import time

from django.utils.translation import ugettext as _

from base_cloud.clients.cinder_client import Client as cnd_client
from base_cloud.utils import LazyLoader
from base_cloud.utils import logger_decorator, handle_error

LOG = logging.getLogger(__name__)
ATTEMPTS = 600


class StorageAction(object):
    def __init__(self):
        super(StorageAction, self).__init__()
        self.cinder_cli = LazyLoader(cnd_client)

    @logger_decorator(LOG)
    def create_volume(self, **kwargs):
        try:
            return self.cinder_cli.volume_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create volume with kwargs: {}").format(kwargs)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def check_volume_status(self, volume, delete=True):
        volume_id = volume.id if hasattr(volume, "id") else volume
        volume_name = getattr(volume, "name", None) or volume_id
        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Unable to check volume ({}) status, "
                            "The maximum number of attempts has been "
                            "exceeded.").format(volume_name)
                break
            vol = self.cinder_cli.volume_get(volume_id)
            if vol.status == 'available':
                msg = "Volume {} status active.".format(volume_name)
                LOG.debug(msg)
                return vol
            elif vol.status == "error":
                err_msg = _("Volume {} Status Error.").format(volume_name)
                if delete:
                    self.delete_volume(volume_id)
                break
            LOG.debug("[OPENASTACK] Volume {} status not active. "
                      "Try again ...".format(volume_name))
            attempts -= 1
            time.sleep(2)
        handle_error(err_msg)

    def check_volume_snapshot_status(self, snapshot):
        snapshot_id = snapshot.id if hasattr(snapshot, "id") else snapshot
        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Unable to check volume snapshot ({}) status, "
                            "The maximum number of attempts has been "
                            "exceeded.").format(snapshot_id)
                break
            snap = self.cinder_cli.snapshot_get(snapshot_id)
            if snap.status == 'available':
                msg = "[OPENSTACK] Volume snapshot {} status active.".format(snapshot_id)
                LOG.debug(msg)
                return snap
            elif snap.status == "error":
                err_msg = _("Volume snapshot {} Status Error.").format(snapshot_id)
                break
            LOG.debug("[OPENSTACK] Volume snapshot {} status not "
                      "active. Try again ...".format(snapshot_id))
            attempts -= 1
            time.sleep(2)
        handle_error(err_msg)

    @logger_decorator(LOG)
    def get_volume(self, volume_id):
        try:
            return self.cinder_cli.volume_get(volume_id)
        except Exception as e:
            err_msg = _("Unable to get volume {}").format(volume_id)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def delete_volume(self, volume_id, cascade=False, sync=False):
        try:
            self.cinder_cli.volume_delete(volume_id, cascade)
        except Exception as e:
            err_msg = _("Scheduled Delete a volume {}").format(volume_id)
            handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.cinder_cli.volume_get(volume_id)
                except Exception as e:
                    LOG.info("Deleted volume {}".format(volume_id))
                    break
                attempts -= 1
                time.sleep(1)
        return True

    @logger_decorator(LOG)
    def update_volume(self, volume_id, **kwargs):
        try:
            return self.cinder_cli.volume_update(volume_id, **kwargs)
        except Exception as e:
            err_msg = _("Unable to update volume {}").format(volume_id)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def list_volumes(self, **kwargs):
        try:
            return self.cinder_cli.volume_list(**kwargs)
        except Exception as e:
            err_msg = _("Unable to list volumes {}").format(kwargs)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def list_volume_snapshots(self, **kwargs):
        try:
            return self.cinder_cli.snapshot_list(**kwargs)
        except Exception as e:
            err_msg = _("Unable to list volumes {}").format(kwargs)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def delete_volume_snapshot(self, snap_id, force=True, is_async=True):
        try:
            self.cinder_cli.snapshot_delete(snap_id, force)
        except Exception as e:
            err_msg = _("Unable to delete volume snapshot {}").format(snap_id)
            handle_error(err_msg, e)

        if not is_async:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.cinder_cli.snapshot_get(snap_id)
                except Exception:
                    LOG.info("Deleted volume snapshot {}".format(snap_id))
                    break
                time.sleep(0.5)

    @logger_decorator(LOG)
    def get_volume_snapshot(self, snap_id):
        try:
            return self.cinder_cli.snapshot_get(snap_id)
        except Exception as e:
            err_msg = _("Unable to get volume snapshot {}").format(snap_id)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def create_volume_snapshot(self, **kwargs):
        try:
            return self.cinder_cli.snapshot_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create volume snapshot")
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def attach_volumes(self, volume_id, instance_uuid, mountpoint):
        try:
            return self.cinder_cli.volume_attach(volume_id,
                                                 instance_uuid,
                                                 mountpoint)
        except Exception as e:
            err_msg = _("Unable to attach volume {} to "
                        "instance {}").format(volume_id, instance_uuid)
            handle_error(err_msg, e)

    @logger_decorator(LOG)
    def detach_volumes(self, volume_id):
        try:
            return self.cinder_cli.volume_detach(volume_id)
        except Exception as e:
            err_msg = _("Unable to detach volume {}").format(volume_id)
            handle_error(err_msg, e)
