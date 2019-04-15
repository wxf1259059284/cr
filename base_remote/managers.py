# -*- coding: utf-8 -*-
import logging
import uuid

from django.utils import six

from base_auth.models import User

from base_remote.utils.guacamole import GuacamoleDatabase, GuacamoleServer, GuacamoleConsumer


from base_remote import app_settings


logger = logging.getLogger(__name__)


class RemoteManager(object):

    def __init__(self, user=None, host=None, server=None):
        if host and not server:
            server = get_remote_server(host)

        self.guacamole_db = GuacamoleDatabase()
        self.guacamole_server = GuacamoleServer(server)

        if user:
            if isinstance(user, User):
                pass
            elif isinstance(user, (six.integer_types, six.string_types, six.text_type)):
                user = User.objects.get(pk=user)
            else:
                raise Exception('invalid user')

            self.guacamole_consumer = GuacamoleConsumer(user, server)
        else:
            self.guacamole_consumer = None

    def remove_user(self, user_id):
        self.guacamole_db.remove_user(user_id)

    def get_connection_url(self, relation_id):
        return self.guacamole_server.get_connection_url(relation_id)

    def get_ssh_connection_url(self, relation_id):
        return self.get_connection_url(relation_id)

    def get_rdp_connection_url(self, relation_id):
        return self.get_connection_url(relation_id)

    def remove_connection(self, relation_id):
        return self.guacamole_db.remove_connection(relation_id)

    def remove_ssh_connection(self, relation_id):
        return self.remove_connection(relation_id)

    def remove_rdp_connection(self, relation_id):
        return self.remove_connection(relation_id)

    def enable_recording(self, relation_id, recording_name=None):
        recording_name = recording_name or str(uuid.uuid4())
        return self.guacamole_db.enable_recording(relation_id, recording_name)

    def disable_recording(self, relation_id):
        return self.guacamole_db.disable_recording(relation_id)

    def get_recording_name(self, relation_id):
        return self.guacamole_db.get_recording_name(relation_id)

    def is_enable_recording(self, relation_id):
        return self.guacamole_db.is_enable_recording(relation_id)

    def convert_recording(self, recording_name, screen_size='1366x768', callback_script=''):
        return self.guacamole_server.convert_recording(recording_name, screen_size=screen_size,
                                                       callback_script=callback_script)

    def _check_guacamole_consumer(self):
        if not self.guacamole_consumer:
            raise Exception('no user')

    def login_guacamole(self, response=None):
        self._check_guacamole_consumer()
        return self.guacamole_consumer.login(response)

    def create_ssh_connection(self, connection_name, hostname, **kwargs):
        self._check_guacamole_consumer()
        return self.guacamole_consumer.create_ssh_connection(connection_name, hostname, **kwargs)

    def create_ssh_connections(self, params):
        self._check_guacamole_consumer()
        return self.guacamole_consumer.create_ssh_connections(params)

    def create_rdp_connection(self, connection_name, hostname, **kwargs):
        self._check_guacamole_consumer()
        return self.guacamole_consumer.create_rdp_connection(connection_name, hostname, **kwargs)

    def create_rdp_connections(self, params):
        self._check_guacamole_consumer()
        return self.guacamole_consumer.create_rdp_connections(params)


fake_guacadmin = User(
    id=app_settings.GUACADMIN_USER['id'],
    username=app_settings.GUACADMIN_USER['username'],
    password=app_settings.GUACADMIN_USER['password'],
)


class MonitorManager(object):

    def __init__(self, host=None, server=None):
        if host and not server:
            server = get_remote_server(host)
        self.guacamole_admin = GuacamoleConsumer(fake_guacadmin, server)

    def share_active_sessions_for_monitor(self, connection_ids):
        return self.guacamole_admin.share_active_sessions_for_monitor(connection_ids)

    def share_active_sessions_for_assistance(self, connection_ids):
        return self.guacamole_admin.share_active_sessions_for_assistance(connection_ids)


guacamole_host_server = {}
for server in app_settings.GUACAMOLE_SERVERS:
    guacamole_host_server[server['host_ip']] = server['server']


def get_remote_server(host_ip):
    return guacamole_host_server.get(host_ip)
