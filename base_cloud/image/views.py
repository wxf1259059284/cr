from __future__ import unicode_literals

import functools
import logging
import time

from django.utils.translation import ugettext as _

from base.utils.functional import cached_property
from base_cloud.clients.glance_client import Client as gl_client
from base_cloud.exception import FriendlyException


LOG = logging.getLogger(__name__)
ATTEMPTS = 300


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


class ImageAction(object):
    def __init__(self):
        super(ImageAction, self).__init__()

    @cached_property
    def glance_cli(self):
        return gl_client()

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")

        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        raise FriendlyException(err_msg)

    @logger_decorator
    def create_image(self, **data):
        meta = self.glance_cli.create_image_metadata(data)

        # Add image source file or URL to metadata
        if (data.get('image_file', None)):
            meta['data'] = data['image_file']
        elif data.get('is_copying'):
            meta['copy_from'] = data['image_url']
        else:
            meta['location'] = data['image_url']

        try:
            image = self.glance_cli.image_create(**meta)
            LOG.info(_('Your image %s has been queued for creation.') %
                     meta['name'])
            return image
        except Exception as e:
            err_msg = _('Unable to create new image')
            # TODO(nikunj2512): Fix this once it is fixed in glance client
            if hasattr(e, 'code') and e.code == 400:
                if "Invalid disk format" in e.details:
                    err_msg = _('Unable to create new image: Invalid disk format '
                                '%s for image.') % meta['disk_format']
                elif "Image name too long" in e.details:
                    err_msg = _('Unable to create new image: Image name too long.')
                elif "not supported" in e.details:
                    err_msg = _('Unable to create new image: URL scheme not '
                                'supported.')
            self._handle_error(err_msg)

    @logger_decorator
    def list_image(self, **kwargs):
        try:
            images = self.glance_cli.image_get_all(**kwargs)
            return images
        except Exception as e:
            err_msg = "Unable to list images."
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_image(self, **kwargs):
        id = kwargs.get("id")
        name = kwargs.get("name")
        if not id and not name:
            err_msg = _("'id' or 'name' must be providered")
            self._handle_error(err_msg)

        if id:
            try:
                return self.glance_cli.image_get_by_id(id)
            except Exception as e:
                err_msg = _("Unable to get image by id {}").format(id)
                self._handle_error(err_msg, e)

        if name:
            try:
                return self.glance_cli.image_get_by_name(name)
            except Exception as e:
                err_msg = _("Unable to get image by name {}").format(name)
                self._handle_error(err_msg, e)

        return None

    @logger_decorator
    def delete_image(self, image_id):
        try:
            self.glance_cli.image_delete(image_id)
            LOG.info("Successfully deleted image {} .".format(image_id))
            return True
        except Exception as e:
            err_msg = "Unable to delete image {}.".format(image_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def update_image(self, image, **kwargs):
        if not image:
            err_msg = _("Image id or name must be providered")
            self._handle_error(err_msg)

        image_obj = self.glance_cli.image_get(image)
        if not image_obj:
            err_msg = _("Unable to get image by '{}'").format(image)
            self._handle_error(err_msg)

        try:
            image = self.glance_cli.image_update(image_obj.id, **kwargs)
            return image
        except Exception as e:
            err_msg = "Unable to update image {}.".format(image)
            self._handle_error(err_msg, e)

    @logger_decorator
    def check_image_status(self, image, type="Image", created=None, failed=None):
        image_id = image.id if hasattr(image, "id") else image
        image_name = getattr(image, "name", None) or image_id
        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Unable to check {} {} status, "
                            "The maximum number of attempts has been "
                            "exceeded.").format(type.lower(), image_name)
                break
            image = self.glance_cli.image_get_by_id(image_id)
            if image.status == "active":
                msg = "{} {} status active.".format(type, image_name)
                LOG.debug(msg)
                if created:
                    created(image)
                return image
            elif image.status == "error":
                err_msg = _("{} {} Status Error.").format(type, image_name)
                if failed:
                    failed(err_msg)
                    self.delete_image(image_id)
                break
            LOG.debug("{} {} status not active. "
                      "Try again ...".format(type, image_name))
            attempts -= 1
            time.sleep(2)
        self._handle_error(err_msg)

    def load_docker_image(self, image):
        if image.get("container_format") == "docker":
            self.check_image_status(image)
            self.glance_cli.docker_image_load(image.id)

    def create_image_by_ftp(self, **kwargs):
        disk_format = kwargs.get("disk_format")
        container_format = kwargs.get("container_format") or "bare"
        if disk_format == "docker":
            disk_format = "raw"
            container_format = "docker"

        try:
            image = self.glance_cli.image_create_by_ftp(
                name=kwargs.get("name"),
                file_name=kwargs.get("file_name"),
                disk_format=disk_format,
                container_format=container_format)

            # load docker image from glance
            # if image:
            #     self.load_docker_image(image)
            return image
        except Exception as e:
            err_msg = _('Unable to create new image')
            self._handle_error(err_msg, e)
