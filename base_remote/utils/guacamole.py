# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import logging
import os
import re
import subprocess
import urllib

from django.db import transaction

from base.utils.functional import cached_property
from base.utils.http import HttpClient
from base.utils.ssh import ssh

from base_remote import app_settings
from base_remote.models import (GuacamoleConnectionGroup, GuacamoleConnection, GuacamoleUser, GuacamoleSharingProfile,
                                GuacamoleConnectionParameter, GuacamoleSharingProfileParameter,
                                GuacamoleConnectionPermission, GuacamoleConnectionGroupPermission,
                                GuacamoleSharingProfilePermission, GuacamoleUserPermission)


logger = logging.getLogger(__name__)


MONITOR_SHARING_PROFILE_NAME = 'cyberpeace_monitor'

ASSISTANCE_SHARING_PROFILE_NAME = 'cyberpeace_assistance'


class GuacamoleDatabase(object):
    # 根据guacamole代码分析调用java类生成无salt密码
    @classmethod
    def create_password_hash(cls, password):
        return hashlib.sha256(password.encode('utf-8')).digest()

    @classmethod
    def add_user(cls, user_id, username, password):
        # 创建密码hash
        password_hash = cls.create_password_hash(password)
        with transaction.atomic():
            # 创建用户
            user = GuacamoleUser.objects.filter(user_id=user_id).first()
            if user:
                user.username = username
                user.password_hash = password_hash
                user.save()
            else:
                user = GuacamoleUser.objects.create(
                    user_id=user_id,
                    username=username,
                    password_hash=password_hash,
                )
            # 设置用户只读权限
            if not GuacamoleUserPermission.objects.filter(
                user_id=user_id,
                affected_user_id=user_id,
                permission=GuacamoleUserPermission.Permission.READ,
            ).exists():
                GuacamoleUserPermission.objects.create(
                    user_id=user_id,
                    affected_user_id=user_id,
                    permission=GuacamoleUserPermission.Permission.READ,
                )
            # 创建对应用户连接组, 把用户id作为连接组id 逻辑上一对一
            group = GuacamoleConnectionGroup.objects.filter(connection_group_id=user_id).first()
            if group:
                group.connection_group_name = username
                group.save()
            else:
                group = GuacamoleConnectionGroup.objects.create(
                    connection_group_id=user_id,
                    connection_group_name=username,
                )
            # 设置连接组只读权限
            if not GuacamoleConnectionGroupPermission.objects.filter(
                user_id=user_id,
                connection_group=group,
                permission=GuacamoleConnectionGroupPermission.Permission.READ
            ).exists():
                GuacamoleConnectionGroupPermission.objects.create(
                    user_id=user_id,
                    connection_group=group,
                    permission=GuacamoleConnectionGroupPermission.Permission.READ
                )
        return user

    # 物理删除用户和连接组
    @classmethod
    def remove_user(cls, user_id):
        with transaction.atomic():
            GuacamoleUser.objects.filter(user_id=user_id).delete()
            GuacamoleConnectionGroup.objects.filter(connection_group_id=user_id).delete()

    # 批量删除
    @classmethod
    def remove_users(cls, user_ids):
        with transaction.atomic():
            GuacamoleUser.objects.filter(user_id__in=user_ids).delete()
            GuacamoleConnectionGroup.objects.filter(connection_group_id__in=user_ids).delete()

    @classmethod
    def add_connection(cls, user_id, connection_name, protocol, config):
        with transaction.atomic():
            # 创建连接, 指定连接所属的连接组为该用户
            connection = GuacamoleConnection.objects.create(
                parent_id=user_id,
                connection_name=connection_name,
                protocol=protocol,
                max_connections=app_settings.GUACADMIN_MAX_CONNECTIONS,
                max_connections_per_user=app_settings.GUACADMIN_MAX_CONNECTIONS_PER_USER,
            )
            # 创建连接参数
            connection_parameters = []
            for name, value in config.items():
                connection_parameters.append(GuacamoleConnectionParameter(
                    connection=connection,
                    parameter_name=name,
                    parameter_value=value,
                ))
            GuacamoleConnectionParameter.objects.bulk_create(connection_parameters)
            # 设置用户的连接权限为只读
            GuacamoleConnectionPermission.objects.create(
                user_id=user_id,
                connection=connection,
                permission=GuacamoleConnectionPermission.Permission.READ
            )
            # 创建共享连接配置：只读监控
            monitor_sharing_profile = GuacamoleSharingProfile.objects.create(
                sharing_profile_name=MONITOR_SHARING_PROFILE_NAME,
                primary_connection=connection,
            )
            # 只读监控参数配置
            GuacamoleSharingProfileParameter.objects.create(
                sharing_profile=monitor_sharing_profile,
                parameter_name='read-only',
                parameter_value='true',
            )
            # 共享连接配置权限，所有者只读
            GuacamoleSharingProfilePermission.objects.create(
                user_id=user_id,
                sharing_profile=monitor_sharing_profile,
                permission=GuacamoleConnectionPermission.Permission.READ,
            )
            # 创建共享连接配置：远程协助
            assistance_sharing_profile = GuacamoleSharingProfile.objects.create(
                sharing_profile_name=ASSISTANCE_SHARING_PROFILE_NAME,
                primary_connection=connection,
            )
            # 共享连接配置权限，所有者只读
            GuacamoleSharingProfilePermission.objects.create(
                user_id=user_id,
                sharing_profile=assistance_sharing_profile,
                permission=GuacamoleConnectionPermission.Permission.READ,
            )

        return connection

    # 批量添加连接
    @classmethod
    def add_connections(cls, connection_params):
        connections = []
        with transaction.atomic():
            for param in connection_params:
                connection = cls.add_connection(
                    user_id=param['user_id'],
                    connection_name=param['connection_name'],
                    protocol=param['protocol'],
                    config=param['config'],
                )
                connections.append(connection)
        return connections

    @classmethod
    def remove_connection(cls, connection_id):
        GuacamoleConnection.objects.filter(connection_id=connection_id).delete()

    @classmethod
    def remove_connections(cls, connection_ids):
        GuacamoleConnection.objects.filter(connection_id__in=connection_ids).delete()

    @classmethod
    def _get_connection_parameter(cls, connection_id, name):
        parameters = GuacamoleConnectionParameter.objects.filter(
            connection=connection_id,
            parameter_name=name,
        ).values('parameter_value')

        if len(parameters) > 0:
            return parameters[0]['parameter_value']
        else:
            return None

    @classmethod
    def _set_connection_parameter(cls, connection_id, name, value, keep_origin=False):
        if GuacamoleConnectionParameter.objects.filter(
            connection=connection_id,
            parameter_name=name,
        ).exists():
            if not keep_origin:
                GuacamoleConnectionParameter.objects.filter(
                    connection=connection_id,
                    parameter_name=name,
                ).update(
                    parameter_value=value,
                )
        else:
            GuacamoleConnectionParameter.objects.create(
                connection_id=connection_id,
                parameter_name=name,
                parameter_value=value,
            )

    @classmethod
    def _del_connection_parameter(cls, connection_id, name):
        GuacamoleConnectionParameter.objects.filter(
            connection=connection_id,
            parameter_name=name,
        ).delete()

    @classmethod
    def enable_recording(cls, connection_id, recording_name):
        cls._set_connection_parameter(connection_id, 'recording-path', app_settings.RECORDING_SOURCE_PATH)
        cls._set_connection_parameter(connection_id, 'recording-name', recording_name, keep_origin=True)
        cls._set_connection_parameter(connection_id, 'create-recording-path', 'true')

    @classmethod
    def get_recording_name(cls, connection_id):
        return cls._get_connection_parameter(connection_id, 'recording-name')

    @classmethod
    def disable_recording(cls, connection_id):
        cls._del_connection_parameter(connection_id, 'recording-path')
        cls._del_connection_parameter(connection_id, 'recording-name')
        cls._del_connection_parameter(connection_id, 'create-recording-path')

    @classmethod
    def is_enable_recording(cls, connection_id):
        if cls._get_connection_parameter(connection_id, 'recording-path'):
            return True
        else:
            return False


class GuacamoleServer(object):
    server_public_server = {}
    for server in app_settings.GUACAMOLE_SERVERS:
        server_public_server[server['server']] = server['public_server']

    def __init__(self, server=None):
        self.server = server or app_settings.GUACAMOLE_SERVERS[0]['server']
        self.public_server = self.server_public_server[self.server]

    @cached_property
    def api_http(self):
        return HttpClient(app_settings.GUACAMOLE_API_URL_PREFIX.format(server=self.server), timeout=5)

    def api_get(self, url, data):
        return self.api_http.mget(self.api_http.murl(url), params=data)

    def api_post(self, url, data):
        return self.api_http.mpost(self.api_http.murl(url), data=data)

    # 分析guacamole连接url, 根据连接id生成连接url
    def get_connection_url(self, connection_id):
        client_name = base64.b64encode('%s\x00c\x00mysql' % connection_id)
        connection_url = app_settings.GUACAMOLE_CONNECTION_URL.format(
            server=self.public_server,
            client_name=client_name
        )
        return connection_url

    # 批量生成连接url
    def get_connection_urls(self, connection_ids):
        urls = {}
        for connection_id in connection_ids:
            urls[connection_id] = self.get_connection_url(connection_id)
        return urls

    def get_shared_active_session_url(self, key):
        client_name = base64.b64encode('%s\x00c\x00mysql-shared' % key)
        return app_settings.GUACAMOLE_PATH_SHARED_ACTIVE_SESSION.format(
            server=self.public_server,
            client_name=client_name,
            key=key,
        )

    @classmethod
    def scan_recording(self, recording_name):
        mp4_names = []

        mp4_name_pattern = re.compile(r'^{recording_name}(.\d+)?.m4v.mp4$'.format(recording_name=recording_name))
        for filename in os.listdir(app_settings.RECORDING_PATH):
            if mp4_name_pattern.match(filename):
                mp4_names.append(filename)
        return mp4_names

    def convert_recording(self,
                          recording_name,
                          screen_size='1366x768',
                          bitrate=2000000,
                          callback_script=''):

        # fix screen_size
        screen_sizes = screen_size.split('x')
        try:
            screen_width = int(screen_sizes[0])
            screen_height = int(screen_sizes[1])
            screen_width_remainder = screen_width % 32
            if screen_width_remainder != 0:
                screen_width = screen_width - screen_width_remainder

            screen_height_remainder = screen_height % 2
            if screen_height_remainder != 0:
                screen_height = screen_height - screen_height_remainder
        except Exception:
            return []
        else:
            screen_size = '{width}x{height}'.format(width=screen_width, height=screen_height)

        guacamole_server_mapping = {}
        for server in app_settings.GUACAMOLE_SERVERS:
            guacamole_server_mapping[server['server']] = server
        server = guacamole_server_mapping.get(self.server)
        if not server:
            return False

        mp4_names = []
        recording_source_path = app_settings.RECORDING_SOURCE_PATH
        recording_path = app_settings.RECORDING_PATH

        if server['host_ip'] == app_settings.OJ_SERVER['host_ip']:
            s2m4v_command = 'guacenc -s {screen_size} -r {bitrate} -f {file}'.format(
                screen_size=screen_size,
                bitrate=bitrate,
                file='%s*' % os.path.join(recording_source_path, recording_name),
            )
            try:
                subprocess.check_call(s2m4v_command, shell=True)
            except subprocess.CalledProcessError as e:
                logger.error('guacamole convert session recording error: command[%s], error[%s]', s2m4v_command, e)
                return []

            m4v_names = []
            recording_name_pattern = re.compile(r'^{recording_name}(.\d+)?$'.format(recording_name=recording_name))
            m4v_name_pattern = re.compile(r'^{recording_name}(.\d+)?.m4v$'.format(recording_name=recording_name))
            for filename in os.listdir(recording_source_path):
                if m4v_name_pattern.match(filename):
                    m4v_names.append(filename)

                elif recording_name_pattern.match(filename):
                    os.remove(os.path.join(recording_source_path, filename))

            mp4_names = []
            for m4v_name in m4v_names:
                m4v_file = os.path.join(recording_source_path, m4v_name)
                mp4_name = m4v_name + '.mp4'
                mp4_file = os.path.join(recording_path, mp4_name)
                m4v2mp4_command = 'ffmpeg -i {m4v_file} {mp4_file}'.format(
                    m4v_file=m4v_file,
                    mp4_file=mp4_file,
                )
                try:
                    subprocess.check_call(m4v2mp4_command, shell=True)
                except subprocess.CalledProcessError as e:
                    logger.error('guacamole convert session recording error: command[%s], error[%s]', m4v2mp4_command,
                                 e)
                else:
                    os.remove(m4v_file)
                    mp4_names.append(mp4_name)
        else:
            convert_command_template = r'\n'.join([
                "",
                r"guacenc -s {screen_size} -r {bitrate} -f {recording_source_path}/{recording_name}*",
                r"find {recording_source_path} -type f  "
                r"-regextype egrep -regex '^{recording_source_path}/{recording_name}(.[0-9]+)?$' "
                r"-exec  rm -f {{}} \;",
                r"find {recording_source_path} -type f  "
                r"-regextype egrep -regex '^{recording_source_path}/{recording_name}(.[0-9]+)?.m4v$' "
                r"-exec  ffmpeg -i {{}} {{}}.mp4 \;",
                r"find {recording_source_path} -type f  "
                r"-regextype egrep -regex '^{recording_source_path}/{recording_name}(.[0-9]+)?.m4v$' "
                r"-exec  rm -f {{}} \;",
                r"find {recording_source_path} -type f  "
                r"-regextype egrep -regex '^{recording_source_path}/{recording_name}(.[0-9]+)?.m4v.mp4$' "
                r"-exec  sshpass -p {self_ssh_pass} scp {{}} {self_ssh_user}@{self_ssh_host}:{recording_path} \;",
                r"find {recording_source_path} -type f  "
                r"-regextype egrep -regex '^{recording_source_path}/{recording_name}(.[0-9]+)?.m4v.mp4$' "
                r"-exec  rm -f {{}} \;",
                "",
            ])
            if callback_script:
                convert_command_template = convert_command_template + callback_script

            convert_command = convert_command_template.format(
                screen_size=screen_size,
                bitrate=bitrate,
                recording_source_path=recording_source_path,
                recording_path=recording_path,
                recording_name=recording_name,
                self_ssh_host=app_settings.OJ_SERVER['host_ip'],
                self_ssh_user=app_settings.OJ_SERVER['ssh_username'],
                self_ssh_pass=app_settings.OJ_SERVER['ssh_password'],
            )

            convert_command_hidden = convert_command_template.format(
                screen_size=screen_size,
                bitrate=bitrate,
                recording_source_path=recording_source_path,
                recording_path=recording_path,
                recording_name=recording_name,
                self_ssh_host=app_settings.OJ_SERVER['host_ip'],
                self_ssh_user=app_settings.OJ_SERVER['ssh_username'],
                self_ssh_pass='******',
            )

            logger.info('guacamole[%s] convert session recording start: command[%s]', server['host_ip'],
                        convert_command_hidden)
            try:
                sc = ssh(server['host_ip'], 22, server['ssh_username'], server['ssh_password'])
                sc.exe(convert_command, timeout=3600 * 2)
            except Exception as e:
                logger.error('guacamole[%s] convert session recording error: command[%s], error[%s]', server['host_ip'],
                             convert_command_hidden, e)

        return mp4_names


class GuacamoleConsumer(object):

    def __init__(self, user, server=None):
        self.user = user
        self.user_id = user.id
        self.username = user.username
        self.password = user.password
        self.db = GuacamoleDatabase()
        self.server = GuacamoleServer(server)
        self._check_user()

    def _check_user(self):
        if not GuacamoleUser.objects.filter(user_id=self.user_id).exists() or \
                not GuacamoleConnectionGroup.objects.filter(connection_group_id=self.user_id).exists():
            self.db.add_user(self.user_id, self.username, self.password)
        return True

    # 同步项目的用户和guacamole的用户
    def sync_user(self):
        return self.db.add_user(self.user_id, self.username, self.password)

    def delete_user(self):
        self.db.remove_user(self.user_id)

    def _login(self, response=None):
        content = self._get_token()
        if content and response:
            response.set_cookie('GUAC_AUTH', urllib.quote(content), path=app_settings.GUACAMOLE_COOKIE_PATH)
        return content

    def login(self, response=None):
        content = self._login(response)
        if not content:
            self.sync_user()
            content = self._login(response)
        return response if response else content

    def _get_token(self):
        data = {
            'username': self.username,
            'password': self.password,
        }
        res = self.server.api_post(app_settings.GUACAMOLE_API_PATH_TOKENS, data)
        if res.status_code == 200:
            return res.content
        else:
            logger.error('guacamole user[%s] get token with data[%s] failed', self.username, data)
            return None

    def _get_token_str(self):
        content = self._get_token()
        if content:
            return json.loads(content).get('authToken')
        else:
            return None

    def _get_active_sessions(self):
        token = self._get_token_str()
        if not token:
            return None

        data = {'token': token}
        res = self.server.api_get(app_settings.GUACAMOLE_API_PATH_ACTIVE_SESSIONS, data)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error('guacamole user[%s] get active sessions failed', self.username)
            return None

    # 这里过滤只获取用户自己创建并连接的会话(排除了用户共享的session)
    def _get_connection_active_sessions(self, connection_ids=None):
        active_sessions = self._get_active_sessions()
        if not active_sessions:
            return {}

        # 获取活动连接的所有者用户
        active_session_connection_ids = set()
        for session_id, detail in active_sessions.items():
            active_session_connection_ids.add(detail['connectionIdentifier'])
        connections = GuacamoleConnection.objects.exclude(parent=None).filter(
            connection_id__in=active_session_connection_ids)
        connection_user_ids = [connection.parent_id for connection in connections]
        connection_users = GuacamoleUser.objects.filter(user_id__in=connection_user_ids)
        connection_user_id_username_map = {user.user_id: user.username for user in connection_users}
        connection_id_username_map = {connection.connection_id: connection_user_id_username_map[connection.parent_id]
                                      for connection in connections}

        # 从活动连接中筛选出连接所有者自己的会话, 只取第一个会话, (不考虑自己访问自己共享的连接产生的会话)
        connection_id_session_map = {}
        for session_id, session in active_sessions.items():
            connection_id = int(session['connectionIdentifier'])
            parent_username = connection_id_username_map.get(connection_id)
            if (parent_username
                    and session['username'] == parent_username and connection_id not in connection_id_session_map):
                connection_id_session_map[connection_id] = session
        if not connection_ids:
            return connection_id_session_map
        else:
            filter_connection_id_session_map = {}
            for connection_id in connection_ids:
                session = connection_id_session_map.get(connection_id)
                if session:
                    filter_connection_id_session_map[connection_id] = session
            return filter_connection_id_session_map

    def _share_active_session(self, session_id, sharing_profile_id):
        token = self._get_token_str()
        if not token:
            return None

        data = {'token': token}
        res = self.server.api_get(
            app_settings.GUACAMOLE_API_PATH_SHARE_ACTIVE_SESSION.format(
                session_id=session_id,
                sharing_profile_id=sharing_profile_id,
            ),
            data
        )
        if res.status_code == 200:
            return res.json().get('values', {}).get('key')
        else:
            logger.error('guacamole user[%s] share active session[%s] sharing_profile_id[%s] failed', self.username,
                         session_id, sharing_profile_id)
            return None

    def share_active_sessions(self, connection_ids, sharing_profile_name=None, return_type='url'):
        active_sessions = self._get_connection_active_sessions(connection_ids)
        if not active_sessions:
            return {}

        sharing_profiles = GuacamoleSharingProfile.objects.filter(
            primary_connection__in=connection_ids,
        )
        if sharing_profile_name:
            sharing_profiles = sharing_profiles.filter(
                sharing_profile_name=sharing_profile_name
            )
        connection_id_sharing_profiles_map = {}
        for sharing_profile in sharing_profiles:
            connection_id_sharing_profiles_map.setdefault(sharing_profile.primary_connection_id, []).append(
                sharing_profile)

        connection_shared_key = {}
        for connection_id, session in active_sessions.items():
            sharing_profile_list = connection_id_sharing_profiles_map.get(connection_id)
            if sharing_profile_list:
                name_shared_key_map = {}
                for sharing_profile in sharing_profile_list:
                    shared_key = self._share_active_session(session['identifier'], sharing_profile.sharing_profile_id)
                    if return_type == 'url':
                        result = self.server.get_shared_active_session_url(shared_key) if shared_key else None
                    else:
                        result = shared_key
                    name_shared_key_map[sharing_profile.sharing_profile_name] = result
                connection_shared_key[connection_id] = name_shared_key_map
        return connection_shared_key

    def share_active_sessions_for_monitor(self, connection_ids):
        ret = self.share_active_sessions(connection_ids, MONITOR_SHARING_PROFILE_NAME)
        data = {}
        for connection_id, r in ret.items():
            data[connection_id] = r[MONITOR_SHARING_PROFILE_NAME]
        return data

    def share_active_sessions_for_assistance(self, connection_ids):
        ret = self.share_active_sessions(connection_ids, ASSISTANCE_SHARING_PROFILE_NAME)
        data = {}
        for connection_id, r in ret.items():
            data[connection_id] = r[ASSISTANCE_SHARING_PROFILE_NAME]
        return data

    def _generate_add_ssh_connection_param(self, connection_name, hostname, **kwargs):
        protocol = 'ssh'
        config = {
            'color-scheme': 'white-black',
            'font-name': 'Yahei Mono',
            'hostname': hostname,
            'port': kwargs.get('port', 22),
            'enable-sftp': kwargs.get('enable-sftp', 'true'),
        }
        username = kwargs.get('username', None)
        password = kwargs.get('password', None)
        private_key = kwargs.get('private_key', None)
        passphrase = kwargs.get('passphrase', None)
        if username:
            config['username'] = username
        if password:
            config['password'] = password
        if private_key:
            config['private-key'] = private_key
        if passphrase:
            config['passphrase'] = passphrase
        connection_param = {
            'user_id': self.user_id,
            'connection_name': connection_name,
            'protocol': protocol,
            'config': config,
        }
        return connection_param

    def _generate_add_vnc_connection_param(self, connection_name, hostname, port, **kwargs):
        protocol = 'vnc'
        config = {
            'hostname': hostname,
            'port': port,
        }
        password = kwargs.get('password', None)
        if password:
            config['password'] = password
        connection_param = {
            'user_id': self.user_id,
            'connection_name': connection_name,
            'protocol': protocol,
            'config': config,
        }
        return connection_param

    def _generate_add_rdp_connection_param(self, connection_name, hostname, **kwargs):
        protocol = 'rdp'
        config = {
            'hostname': hostname,
            'port': kwargs.get('port', 3389),
            'security': kwargs.get('security', 'rdp'),
            'ignore-cert': kwargs.get('ignore-cert', 'true'),
            'color-depth': kwargs.get('color-depth', '32'),

            # performance
            'enable-desktop-composition': kwargs.get('enable-desktop-composition', 'true'),
            'enable-font-smoothing': kwargs.get('enable-font-smoothing', 'true'),
            'enable-full-window-drag': kwargs.get('enable-full-window-drag', 'true'),
            'enable-menu-animations': kwargs.get('enable-menu-animations', 'true'),
            'enable-theming': kwargs.get('enable-theming', 'true'),
            'enable-wallpaper': kwargs.get('enable-wallpaper', 'true'),

            'enable-audio-input': kwargs.get('enable-audio-input', 'true'),
            'enable-printing': kwargs.get('enable-printing', 'true'),
        }

        username = kwargs.get('username', None)
        password = kwargs.get('password', None)
        if username:
            config['username'] = username
        if password:
            config['password'] = password

        enable_sftp = kwargs.get('enable-sftp', 'false')
        if enable_sftp == 'true':
            config['enable-sftp'] = enable_sftp
            config['sftp-hostname'] = hostname
            config['sftp-port'] = kwargs.get('sftp-port', 22)
            sftp_username = kwargs.get('sftp-username', None)
            if sftp_username:
                sftp_password = kwargs.get('sftp-password', None)
            else:
                sftp_username = username
                sftp_password = password
            sftp_private_key = kwargs.get('sftp-private-key', None)
            sftp_passphrase = kwargs.get('sftp-passphrase', None)
            if sftp_username:
                config['sftp-username'] = sftp_username
            if sftp_password:
                config['sftp-password'] = sftp_password
            if sftp_private_key:
                config['sftp-private-key'] = sftp_private_key
            if sftp_passphrase:
                config['sftp-passphrase'] = sftp_passphrase
        else:
            config.update({
                'enable-drive': kwargs.get('enable-drive', 'true'),
                'drive-path': kwargs.get('drive-path', os.path.join(app_settings.GUACDRIVE_PATH, connection_name)),
                'create-drive-path': kwargs.get('create-drive-path', 'true'),
            })

        connection_param = {
            'user_id': self.user_id,
            'connection_name': connection_name,
            'protocol': protocol,
            'config': config,
        }
        return connection_param

    def create_ssh_connection(self, connection_name, hostname, **kwargs):
        connection_param = self._generate_add_ssh_connection_param(connection_name, hostname, **kwargs)
        return self.db.add_connection(**connection_param)

    def create_vnc_connection(self, connection_name, hostname, port, **kwargs):
        connection_param = self._generate_add_vnc_connection_param(connection_name, hostname, port, **kwargs)
        return self.db.add_connection(**connection_param)

    def create_rdp_connection(self, connection_name, hostname, **kwargs):
        connection_param = self._generate_add_rdp_connection_param(connection_name, hostname, **kwargs)
        return self.db.add_connection(**connection_param)

    def _create_connections(self, params, generate_param):
        connection_params = []
        for param in params:
            connection_param = generate_param(**param)
            connection_params.append(connection_param)

        return self.db.add_connections(connection_params)

    def create_ssh_connections(self, params):
        return self._create_connections(params, self._generate_add_ssh_connection_param)

    def create_vnc_connections(self, params):
        return self._create_connections(params, self._generate_add_vnc_connection_param)

    def create_rdp_connections(self, params):
        return self._create_connections(params, self._generate_add_rdp_connection_param)
