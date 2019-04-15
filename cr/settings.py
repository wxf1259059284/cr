# -*- coding: utf-8 -*-
import os
import sys

from django.utils.translation import ugettext_lazy as _

from .config import (
    DEBUG,
    PUBLIC_SERVER_PROTOCOL,
    PUBLIC_SERVER_IP,
    PUBLIC_SERVER_PORT,
    SERVER_PROTOCOL,
    SERVER_IP,
    SERVER_PORT,
    VIS_HOST,
    CORS_ORIGIN_WHITELIST,
    APP_PATHS,
    APP_SETTINGS,
    DATABASES,
    ENABLE_API_CACHE,
    REDIS_PASS,
    MAX_BUMBER_ATTEMPTS,
)


reload(sys)
sys.setdefaultencoding('utf8')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'b=r1besx*5po3s*#-02de&csk=c82$^9dqtehp7^du@7gc=q77'

ALLOWED_HOSTS = ['*']


SERVER = '{}://{}:{}'.format(SERVER_PROTOCOL, SERVER_IP, SERVER_PORT)
PUBLIC_SERVER = '{}://{}:{}'.format(PUBLIC_SERVER_PROTOCOL, PUBLIC_SERVER_IP, PUBLIC_SERVER_PORT)

# 本项目未用到
RESOURCE_SERVER = ''
USE_CDN = False


APPS = []
APP_PATH = {}
APP_NAMES = []
for app_path in APP_PATHS:
    if isinstance(app_path, tuple):
        app_name = app_path[0]
        app_path = app_path[1]
    else:
        app_name = app_path
        app_path = app_path

    APPS.append('{}.apps.AppConfig'.format(app_name))
    APP_PATH[app_name] = app_path
    APP_NAMES.append(app_name)


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'channels',
    'channels.delay',
]
INSTALLED_APPS.extend(APPS)


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'cached_auth.Middleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'cr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cr.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

LANGUAGES = [
    ('zh-hans', _('Chinese')),
    ('en', _('English')),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

STATIC_V_DIRS = {app_name: os.path.join(BASE_DIR, app_name) for app_name in APP_NAMES}


MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Session
SESSION_COOKIE_NAME = 'cr_sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = False
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
CSRF_COOKIE_NAME = 'cr_csrftoken'


AUTH_USER_MODEL = 'base_auth.User'


DEFAULT_CACHE_AGE = 300
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
            # "hosts": ["redis://:{}@127.0.0.1:6379/0".format(REDIS_PASS)],
            "prefix": u"cr",
            "expiry": 60 * 10,
            "capacity": 8192,
        },
        "ROUTING": "cr.routers.routerpatterns",
    },
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)s %(asctime)s %(module)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'logfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'log/log.log'),
            'formatter': 'standard',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'logfile']
    },
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.StaticHTMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),

    'EXCEPTION_HANDLER': 'base.utils.rest.views.exception_handler',

    'ORDERING_PARAM': 'sort',

    # Input and output formats (关闭时区设置以下)
    'DATE_FORMAT': '%Y-%m-%d',
    'DATE_INPUT_FORMATS': ('%Y-%m-%d',),

    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATETIME_INPUT_FORMATS': ('%Y-%m-%d %H:%M:%S',),

    'TIME_FORMAT': '%H:%M:%S',
    'TIME_INPUT_FORMATS': ('%H:%M:%S',),
}

SUB_MODULES = {
    'public': '',
    'cms': 'admin',
    'web': '',
}

ENCODING = 'utf-8'

MS = {}

RPC_DEFAULT_HOST = "127.0.0.1"
RPC_DEFAULT_PORT = 8192

SOCKET_TIMEOUT = 10000
CONNECT_TIMEOUT = 10000

DOWNLOAD_SERVER = 'http://169.254.169.254/cr'


__all__ = [
    'DEBUG',
    'PUBLIC_SERVER_PROTOCOL',
    'PUBLIC_SERVER_IP',
    'PUBLIC_SERVER_PORT',
    'SERVER_PROTOCOL',
    'SERVER_IP',
    'SERVER_PORT',
    'VIS_HOST',
    'CORS_ORIGIN_WHITELIST',
    'APP_PATHS',
    'APP_SETTINGS',
    'DATABASES',
    'ENABLE_API_CACHE',
    'REDIS_PASS',
    'MAX_BUMBER_ATTEMPTS',
]
