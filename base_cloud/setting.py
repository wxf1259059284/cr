
CONTROLLER_INFO = {
    'ssh_port': 22,
    'ssh_username': 'root',
    'ssh_password': 'ycxx123#',
}

OS_AUTH = {
    'auth_url': 'http://controller:35357/v3/',
    'username': 'admin',
    'password': 'ADMIN_PASS',
    'project_id': 'ea471b7a014b448ababff2d97020e6ba',
    'project_name': 'admin',
    'user_domain_id': 'default',
    'project_domain_id': 'default'
}

COMPLEX_MISC = {
    'external_net': '8a4a30e6-3ec0-4f44-9945-00b341ec9940',
    'linux_flavor': 'linux-middle',
    'windows_flavor': 'windows-middle',
    'security_groups': ['default'],
    'keypairs': '',
    'ftp_path': '/home/ftp',
    'vlan_physical_network': 'vlanprovider',
    'clean_env': False,
    'cpu_allocation_ratio': 16,
    'ram_allocation_ratio': 1.5,
    'disk_allocation_ratio': 1.0,
    'glance_image_dir': '/var/lib/glance/images/',
    'dns_nameservers': ['218.2.135.1'],
    'memcache_host': ['controller:11211'],
}


CONSOLE_PROTOCOL = 'vnc'
CONSOLE_PORT = 6080
CONSOLE_PROXY_PORT = 16080

DONT_SHOW = {
    'instance_list': ["OJ-3.1", 'OJ'],
    'image_list': ["OJ-117", 'OJ-Standard', 'OJ'],
}

CONTROLLER_HTTPD_PORT = 80

RESOURCE_HOSTS = ['127.0.0.1']
