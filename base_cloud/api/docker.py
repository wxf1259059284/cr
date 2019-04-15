# -*- coding: utf-8 -*-
import os
import socket
import subprocess
import time
import uuid

from base.utils.ssh import ssh
from base_proxy.nginx import get_new_valid_port
from base_cloud import app_settings
from base_cloud.complex.views import BaseScene, states, ATTEMPTS

from .utils import str_filter


class Docker(object):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def get(self, container_id, convert_host_ip=True):
        return self.operator.get_container(container_id, convert_host_ip)

    def create(self, **kwargs):
        params = self.load_create_params(**kwargs)
        container = self.send_create(**params)
        container = self.check_create(container, **params)
        return container

    def send_create(self, **params):
        container = self.operator.scene_send_create_container(**params)
        container.id = container.uuid
        return container

    def check_create(self, container, **params):
        container = self.operator.scene_check_create_container(container, **params)
        container.id = container.uuid
        return container

    def create_qos(self, name, container_id=None, network_id=None, rule=None):
        container = self.get(container_id) if container_id else None
        return self.operator.scene_create_qos(name=name, container=container, network_id=network_id, rule=rule)

    def update(self, container_id, **kwargs):
        float_ip = kwargs.get('float_ip')
        if float_ip:
            self.operator.bind_fip(float_ip, port=kwargs.get('fip_port'), instance=self.get(container_id))

    def delete(self, container_id, sync=True, local=False, host=None):
        if local:
            subprocess.call('{docker} stop {name} && {docker} rm {name}'.format(docker=local_docker_cmd(host),
                                                                                name=container_id), shell=True)
        else:
            container = self.get(container_id)
            if container.status == states['RUNNING']:
                self.stop(container_id)
                attempts = ATTEMPTS
                while 1:
                    if attempts <= 0:
                        self.operator.delete_container(container_id, sync, force=False)
                        break
                    container = self.get(container_id)
                    if container.status != states['RUNNING']:
                        self.operator.delete_container(container_id, sync, force=False)
                        break
                    attempts -= 1
                    time.sleep(1)
            else:
                self.operator.delete_container(container_id, sync, force=False)

    def pause(self, container_id, local=False, host=None):
        if local:
            subprocess.call('{docker} pause {name}'.format(docker=local_docker_cmd(host),
                                                           name=container_id), shell=True)
        else:
            self.operator.pause_container(container_id)

    def unpause(self, container_id, local=False, host=None):
        if local:
            subprocess.call('{docker} unpause {name}'.format(docker=local_docker_cmd(host),
                                                             name=container_id), shell=True)
        else:
            self.operator.unpause_container(container_id)

    def start(self, container_id, local=False, host=None):
        if local:
            subprocess.call('{docker} start {name}'.format(docker=local_docker_cmd(host),
                                                           name=container_id), shell=True)
        else:
            self.operator.start_container(container_id)

    def stop(self, container_id, local=False, host=None):
        if local:
            subprocess.call('{docker} stop {name}'.format(docker=local_docker_cmd(host),
                                                          name=container_id), shell=True)
        else:
            self.operator.stop_container(container_id)

    def restart(self, container_id, local=False, host=None):
        if local:
            subprocess.call('{docker} restart {name}'.format(docker=local_docker_cmd(host),
                                                             name=container_id), shell=True)
        else:
            self.operator.restart_container(container_id)

    def change_tunnel(self, container_id, tunnel):
        ip = socket.gethostbyname('controller')
        if not ip:
            raise Exception('no controller found')
        sc = ssh(ip,
                 app_settings.CONTROLLER_INFO['ssh_port'],
                 app_settings.CONTROLLER_INFO['ssh_username'],
                 app_settings.CONTROLLER_INFO['ssh_password'])
        sc.exe('/opt/encrypt_links/switch_link.sh {}'.format(tunnel))

    def execute_command(self, container_id, cmd, local=False, host=None):
        if local:
            subprocess.call("{docker} exec {name} '{cmd}'".format(docker=local_docker_cmd(host),
                                                                  name=container_id, cmd=cmd), shell=True)
        else:
            self.operator.execute_container_cmd(container_id, cmd)

    def load_create_params(self, **kwargs):
        '''
            name: 名称
            image: 创建机器的镜像
            flavor: 云主机类型
            system_type: 系统类型
            networks: [{
                'net_id': 'xxxx',
                'fixed_ip': 'xxxx',
            }, {
                'net_id': 'xxxx',
                'fixed_ip': 'xxxx',
            }, {
                'port_id': 'xxxx',
            }]
            float_ip: 浮动ip
            custom_script: 程序自定义脚本
            init_script: 初始化脚本
            install_script: 安装脚本
            users: [{
                'username': 'xxxxxx',
                'password': '******',
            }]
            report_started: 启动上报参数
            report_inited: 初始化上报参数
        '''
        nics = []
        for network in kwargs.get('networks', []):
            if 'net_id' in network:
                nics.append({
                    'network': network['net_id'],
                    'v4-fixed-ip': network['fixed_ip'],
                })
            elif 'port_id' in network:
                nics.append({
                    'port': network['port_id'],
                })

        params = {
            'name': str_filter(kwargs['name']),
            'image': kwargs['image'],
            'flavor': kwargs['flavor'],
            'system_type': kwargs['system_type'],
            'users': kwargs.get('users'),
            'nics': nics,
            'floating_ip': kwargs.get('float_ip'),
            'attach_url': kwargs.get('attach_url'),
            'custom_script': kwargs.get('custom_script'),
            'init_script': kwargs.get('init_script'),
            'install_script': kwargs.get('install_script'),
            'report_started': kwargs.get('report_started'),
            'report_inited': kwargs.get('report_inited'),
        }

        return params

    def local_create(self, **kwargs):
        container_name = str(uuid.uuid4())
        image = kwargs['image']
        ports = kwargs.get('ports', [])
        port_info = kwargs.get('port_info') or {port: get_new_valid_port() for port in ports}
        port_str = ''
        for port, proxy_port in port_info.items():
            port_str += ' -p {proxy_port}:{port} '.format(port=port, proxy_port=proxy_port)

        host = kwargs.get('host')
        subprocess.call('{docker} run --name {name} -itd {port_str} {image} {local_docker_params}'.format(
            docker=local_docker_cmd(host),
            name=container_name,
            port_str=port_str,
            image=image,
            local_docker_params=local_docker_params(),
        ), shell=True)

        server = type('Container', (object,), {})()
        server.id = container_name
        server.port_info = port_info
        server.host_ip_address = host

        return server


def local_docker_cmd(host=None):
    if host:
        cmd = 'docker -H tcp://{host}'.format(host=host)
    else:
        cmd = 'docker'

    return cmd


def local_docker_params():
    ca_path = '/etc/docker/ssl/ca.pem'
    server_cert_path = '/etc/docker/ssl/server-cert.pem'
    server_key_path = '/etc/docker/ssl/server-key.pem'
    if os.path.exists(ca_path) and os.path.exists(server_cert_path) and os.path.exists(server_key_path):
        return '--tlsverify --tlscacert={} --tlscert={} --tlskey={}'.format(ca_path, server_cert_path, server_key_path)
    else:
        return ''
