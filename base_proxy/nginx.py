# -*- coding: utf-8 -*-
import json
import logging
import os
import random
import re
import socket
import string
import subprocess
import uuid

import psutil

from base_proxy import app_settings


logger = logging.getLogger(__name__)


class NoValidPortException(Exception):
    pass


class InvalidPortException(Exception):
    pass


config_filename_template = '{ip}:{port}.conf'
config_template = ('upstream {name} {{server {ip}:{port};}}server {{listen {proxy_port};'
                   'proxy_connect_timeout {connect_timeout}s;proxy_timeout {timeout}s;proxy_pass {name};}} #{data}')


def generate_config(ip, port, proxy_port=None, timeout=300, connect_timeout=30, name=None):
    if not name:
        name = str(uuid.uuid4())

    if not proxy_port:
        proxy_port = get_new_valid_port()
        if not proxy_port:
            raise NoValidPortException()

    print 'ip %s port %s proxy nginx port is %d' % (ip, port, proxy_port)

    data = {
        'ip': ip,
        'port': port,
        'proxy_port': proxy_port,
        'timeout': timeout,
        'connect_timeout': connect_timeout,
        'name': name,
    }

    config = {
        'config': config_template.format(
            name=name,
            ip=ip,
            port=port,
            proxy_port=proxy_port,
            connect_timeout=connect_timeout,
            timeout=timeout,
            data=json.dumps(data),
        )
    }
    config.update(data)

    return config


def get_config_path(ip, port):
    return os.path.join(app_settings.NGX_CONF_PATH, config_filename_template.format(ip=ip, port=port))


def add_new_proxy(ip, ports, timeout=300, connect_timeout=30, detail=False):
    try:
        ports = map(lambda x: int(x), ports)
    except Exception as e:
        logger.error('load ports[%s] error: %s', ports, e)
        raise InvalidPortException(e.message)

    configs = [add_proxy(ip, port, timeout=timeout, connect_timeout=connect_timeout, detail=detail) for port in ports]
    return configs


def add_proxy(ip, port, proxy_port=None, timeout=300, connect_timeout=30, name=None, detail=False):
    config_path = get_config_path(ip, port)
    if os.path.exists(config_path):
        config = get_proxy(ip, port, detail=True)
        if not config or (proxy_port and config['proxy_port'] != proxy_port):
            delete_proxy(ip, port)
            return add_proxy(ip, port, proxy_port=proxy_port, timeout=timeout, connect_timeout=connect_timeout,
                             name=name)
    else:
        config = generate_config(ip, port, proxy_port=proxy_port, timeout=timeout, connect_timeout=connect_timeout,
                                 name=name)
        with open(config_path, 'wt') as f:
            f.write(config['config'])

    if detail:
        return config
    else:
        return config['proxy_port']


def delete_proxy(ip, port):
    # 删除文件
    os.remove(get_config_path(ip, port))


def get_proxy(ip, port, detail=False):
    config_path = get_config_path(ip, port)
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r') as f:
        config_str = f.read()

    try:
        config = json.loads(config_str.split('#')[1])
    except Exception as e:
        logger.error('get proxy conf[%s] error: %s', config_path, e)
        return None

    config['config'] = config_str
    if detail:
        return config
    else:
        return config['proxy_port']


def exist_proxy(ip, port):
    # 检查是否存在这个ip port的配置文件即可
    return os.path.exists(get_config_path(ip, port))


def get_new_valid_port():
    port = random.randint(app_settings.PROXY_START_PORT, app_settings.PROXY_END_PORT)

    count = 0
    while is_port_open('0.0.0.0', port):
        count = count + 1
        if count >= 10:
            return None
        port = random.randint(app_settings.PROXY_START_PORT, app_settings.PROXY_END_PORT)

    return port


def restart_nginx():
    nginxPid = get_pid('nginx')
    if nginxPid is None:
        subprocess.Popen(app_settings.NGX_START_CMD, shell=True)
    else:
        subprocess.Popen(app_settings.NGX_REBOOT_CMD, shell=True)


def is_port_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, int(port)))
        s.close()
        return True
    except Exception:
        s.close()
        return False


def get_pid(name):
    procs = list(psutil.process_iter())
    regex = r"pid=(\d+),\sname=\'" + name + r"\'"

    pid = 0
    for line in procs:
        process_info = str(line)
        ini_regex = re.compile(regex)
        result = ini_regex.search(process_info)
        if result is not None:
            pid = string.atoi(result.group(1))
            return pid
