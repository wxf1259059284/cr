from __future__ import unicode_literals

import logging
import os
import threading
import time
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import TemporaryUploadedFile

from keystoneauth1.identity import v3
from keystoneauth1 import session
import glanceclient

try:
    from base_cloud import app_settings
except Exception:
    pass
from base_cloud.utils import get_ip_by_hostname, \
    is_uuid_like, get_local_hostname
from base.utils.ssh import ssh


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
        self.glance_client = glanceclient.Client(version=VERSIONS,
                                                 session=sess)

    def image_get_all(self, **kwargs):
        return self.glance_client.images.list(**kwargs)

    def image_get_by_name(self, image_name):
        images = self.image_get_all()
        for image in images:
            if image.name == image_name:
                return image
        return None

    def image_get_by_id(self, image_id):
        return self.glance_client.images.get(image_id)

    def images_list_by_name(self, image_name):
        img_list = []
        images = self.image_get_all()
        for image in images:
            if image.name.startswith(image_name):
                img_list.append(image)
        return img_list

    def image_get(self, image):
        if is_uuid_like(image):
            return self.image_get_by_id(image)
        return self.image_get_by_name(image)

    def image_download(self, image):
        return self.glance_client.images.data(image)

    def create_image_metadata(self, data):
        disk_format = data['disk_format']
        if disk_format in ('ami', 'aki', 'ari',):
            container_format = disk_format
        elif disk_format == 'docker':
            disk_format = 'raw'
            container_format = 'docker'
        elif disk_format == 'ova':
            container_format = 'ova'
            disk_format = 'vmdk'
        else:
            container_format = 'bare'

        meta = {'protected': data.get('protected', False),
                'disk_format': disk_format,
                'container_format': container_format,
                'min_disk': (data['minimum_disk'] or 0),
                'min_ram': (data['minimum_ram'] or 0),
                'name': data['name']}

        is_public = data.get('is_public', data.get('public', True))
        properties = {}
        if data.get('description'):
            properties['description'] = data['description']
        if data.get('kernel'):
            properties['kernel_id'] = data['kernel']
        if data.get('ramdisk'):
            properties['ramdisk_id'] = data['ramdisk']
        if data.get('architecture'):
            properties['architecture'] = data['architecture']

        if int(VERSIONS) < 2:
            meta.update({'is_public': is_public, 'properties': properties})
        else:
            meta['visibility'] = 'public' if is_public else 'private'
            meta.update(properties)

        return meta

    def image_create(self, **kwargs):
        data = kwargs.pop('data', None)
        location = None
        if int(VERSIONS) >= 2:
            location = kwargs.pop('location', None)

        image = self.glance_client.images.create(**kwargs)
        if location is not None:
            self.glance_client.images.add_location(image.id, location, {})

        if data:
            if isinstance(data, TemporaryUploadedFile):
                data.file.close_called = True
            elif isinstance(data, InMemoryUploadedFile):
                data = SimpleUploadedFile(data.name,
                                          data.read(),
                                          data.content_type)
            if int(VERSIONS) < 2:
                t = threading.Thread(target=self.image_update,
                                     args=(image.id,),
                                     kwargs={'data': data})
                t.start()
            else:
                def upload():
                    try:
                        return self.glance_client.images.upload(image.id, data)
                    finally:
                        filename = str(data.file.name)
                        try:
                            os.remove(filename)
                        except OSError as e:
                            LOG.warning('Failed to remove temporary image file '
                                        '%(file)s (%(e)s)',
                                        {'file': filename, 'e': e})

                t = threading.Thread(target=upload)
                t.start()
        return image

    def image_upload(self, image_id, data, remove_source=False):
        try:
            return self.glance_client.images.upload(image_id, data)
        finally:
            if remove_source:
                filename = str(data.file.name)
                try:
                    os.remove(filename)
                except OSError as e:
                    LOG.warning('Failed to remove temporary image file '
                                '%(file)s (%(e)s)',
                                {'file': filename, 'e': e})

    def image_delete(self, image_id):
        self.glance_client.images.delete(image_id)

    def image_update(self, image_id, remove_props=None, **kwargs):
        return self.glance_client.images.update(image_id, remove_props, **kwargs)

    def get_ssh_conn(self, hostname="controller"):
        host_ip = get_ip_by_hostname(hostname)
        return ssh(host_ip,
                   app_settings.CONTROLLER_INFO.get("ssh_port") or 22,
                   app_settings.CONTROLLER_INFO.get("ssh_username") or "root",
                   app_settings.CONTROLLER_INFO.get("ssh_password"),
                   app_settings.CONTROLLER_INFO.get("ssh_key_path"))

    def is_image_file_exists(self, file_name, ftp_path=None):
        if not ftp_path:
            ftp_path = app_settings.COMPLEX_MISC.get("ftp_path")
        image_path = os.path.join(ftp_path, file_name)
        if get_local_hostname() == "controller":
            if os.path.isfile(image_path):
                return True
        else:
            command = "ls {}".format(image_path)
            ssh_conn = self.get_ssh_conn()
            stdin, stdout, stderr = ssh_conn.exe(command=command, timeout=60)
            if stdout.readline().strip() != '':
                return True
        return False

    def image_create_by_ftp(self, name, file_name, ftp_path=None,
                            disk_format="qcow2", container_format="bare"):
        # ssh to controller and execute create command
        if not ftp_path:
            ftp_path = app_settings.COMPLEX_MISC.get("ftp_path")
        image_path = os.path.join(ftp_path, file_name)
        if not self.is_image_file_exists(file_name, ftp_path=None):
            raise Exception("Image not exists ({})".format(image_path))

        image_id = str(uuid.uuid4())
        command = 'export OS_USERNAME={username} && ' \
                  'export OS_PASSWORD={password} && ' \
                  'export OS_PROJECT_NAME={project} && ' \
                  'export OS_USER_DOMAIN_NAME={user_domain} && ' \
                  'export OS_PROJECT_DOMAIN_NAME={project_domain} && ' \
                  'export OS_AUTH_URL={auth_url} && ' \
                  'export OS_IDENTITY_API_VERSION=3 && ' \
                  'export OS_AUTH_VERSION=3 && ' \
                  'openstack image create --file "{file_path}" ' \
                  '--id {image_id} --disk-format {disk_format} ' \
                  '--container-format {container_format} --public ' \
                  '"{image_name}" >> /var/log/ftp_create_image.log 2>&1'.format(
                             username=app_settings.OS_AUTH.get("username"),
                             password=app_settings.OS_AUTH.get("password"),
                             project=app_settings.OS_AUTH.get("project_name"),
                             user_domain=app_settings.OS_AUTH.get("user_domain_id"),
                             project_domain=app_settings.OS_AUTH.get("project_domain_id"),
                             auth_url=app_settings.OS_AUTH.get("auth_url"),
                             image_name=name, file_path=image_path,
                             image_id=image_id, disk_format=disk_format,
                             container_format=container_format)
        ssh_conn = self.get_ssh_conn()
        ssh_conn.exe(command=command, timeout=3600)

        # sleep 5 seconds before get image
        time.sleep(5)
        return self.image_get_by_id(image_id)

    def service_list(self):
        return self.glance_client.services.list()


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="L5uCdcjQQuyY9DLs", project_name="admin",
                 user_domain_id="default", project_domain_id="default")
    img = cli.image_get("bec3567c-9bb9-432a-accd-e20ec28cae57")
    block_device_map = getattr(img, 'block_device_mapping', None)
    import json
    bdm = json.loads(block_device_map)
