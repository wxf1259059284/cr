# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

PUBLIC_SERVER_PROTOCOL = 'http'
PUBLIC_SERVER_IP = '192.168.101.131'
PUBLIC_SERVER_PORT = 80


SERVER_PROTOCOL = 'http'
SERVER_IP = '192.168.101.131'
SERVER_PORT = 8077
VIS_HOST = '127.0.0.1:8050'

CORS_ORIGIN_WHITELIST = ()

APP_PATHS = [
    ('base', ''),
    ('base_auth', 'auth'),
    ('base_remote', 'remote'),
    ('base_proxy', 'proxy'),
    ('base_cloud', 'cloud'),
    ('base_scene', 'scene'),
    ('base_mission', 'mission'),
    ('base_traffic', 'traffic'),
    ('base_monitor', 'monitor'),
    ('base_evaluation', 'evaluation'),
    ('traffic_event', 'traffic_event'),
    ('cr_scene', 'cr_scene'),
    ('dashboard', 'dashboard'),
    ('system', 'system'),
]


APP_SETTINGS = {
    'base_auth': {
        'ORG_DEPTH': 4,
    },
    'base_remote': {
        'DATABASE': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'guacamole_db',
            'USER': 'guacamole_user',
            'PASSWORD': 'guacamole_pass',
            'HOST': '127.0.0.1',
            'PORT': '3306'
        },
        'OJ_SERVER': {
            'host_ip': '192.168.101.131',
            'ssh_username': 'root',
            'ssh_password': '123',
        },
        'GUACAMOLE_SERVERS': (
            {
                'host_ip': '192.168.101.131',
                'public_server': 'http://192.168.101.131:8080',
                'server': 'http://192.168.101.131:8080',
                'ssh_username': 'root',
                'ssh_password': '123',
            },
        )
    },
    'base_cloud': {
        'CONTROLLER_INFO': {
            'ssh_password': 'ycxx123#',
        },
        'OS_AUTH': {
            'project_id': 'fdda50a506db47c5be5ec44c613d0e72',
            'password': 'L5uCdcjQQuyY9DLs',
        },
        'COMPLEX_MISC': {
            'external_net': 'c7667016-3e70-4e97-9ee6-c895eab36408',
        },
        'CONSOLE_PROTOCOL': 'vnc',
        'RESOURCE_HOSTS': ['192.168.100.156'],
    }
}


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cr',
        'USER': 'cr',
        'PASSWORD': 'cr',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

ENABLE_API_CACHE = True
REDIS_PASS = "v105uCdcjQQuCdgww"

MAX_BUMBER_ATTEMPTS = 50
