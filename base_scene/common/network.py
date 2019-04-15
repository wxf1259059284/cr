
from base_cloud import api as cloud
from base_scene.utils.common import random_ips

from .error import error
from .exceptions import SceneException


def random_ip(network):
    ports = cloud.network.get_ports(network.net_id)
    used_ips = []
    for port in ports:
        for ip_info in port['fixed_ips']:
            used_ips.append(ip_info['ip_address'])

    ips = random_ips(network.cidr, 1, exclude_ips=used_ips)
    if len(ips) == 0:
        raise SceneException(error.NO_ENOUGH_IP)
    return ips[0]
