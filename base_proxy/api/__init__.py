
from base_proxy import nginx


def create_proxy(ip, ports, timeout=300):
    if isinstance(ports, (tuple, set, list)):
        return nginx.add_new_proxy(ip, ports, timeout=timeout)
    else:
        return nginx.add_proxy(ip, ports, timeout=timeout)


def delete_proxy(ip, ports):
    if not isinstance(ports, (tuple, set, list)):
        ports = (ports,)

    for port in ports:
        nginx.delete_proxy(ip, port)


def restart_proxy():
    nginx.restart_nginx()
