import os

from importlib import import_module

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings, LazySettings, Settings
from django.conf.urls import include, url
from channels.routing import include as channel_include

from base.utils.thread import async_exe, async_exe_once
from base.utils.rest.routers import rest_path
from base.utils.websocket.routers import ws_path


def get_app_name(module_name):
    return module_name.split('.')[0]


def get_service_name(module_name):
    return module_name.split('.')[1]


def get_app_service_name(module_name):
    return module_name.split('.')


def _get_sub_pattern(path_name):
    if path_name:
        return r'^{path_name}/'.format(path_name=path_name)
    else:
        return r''


def get_app_urls(app_name):
    patterns = {}
    apipatterns = {}
    app_path_name = settings.APP_PATH[app_name]
    app_path = _get_sub_pattern(app_path_name)

    for sub_module_name in settings.SUB_MODULES:
        urls_name = '{app_name}.{sub_module}.urls'.format(
            app_name=app_name,
            sub_module=sub_module_name,
        )
        urls_path = os.path.join(settings.BASE_DIR, urls_name.replace('.', '/') + '.py')
        if os.path.exists(urls_path):
            urls_module = import_module(urls_name)
            urls_module.urlpatterns = getattr(urls_module, 'urlpatterns', [])
            urls_module.apiurlpatterns = getattr(urls_module, 'apiurlpatterns', [])
            if hasattr(urls_module, 'viewsets'):
                urls_module.apiurlpatterns += rest_path(urls_module.viewsets)

            if urls_module.urlpatterns:
                patterns.setdefault(sub_module_name, []).append(
                    url(app_path, include(urls_module.urlpatterns, namespace=app_name))
                )

            if urls_module.apiurlpatterns:
                apipatterns.setdefault(sub_module_name, []).append(
                    url(app_path, include(urls_module.apiurlpatterns, namespace=app_name))
                )

    return patterns, apipatterns


def get_base_urls():
    patterns = []
    apipatterns = []

    app_sub_module_patterns = {}
    app_sub_module_apipatterns = {}
    for app_name in settings.APP_NAMES:
        urls_name = '{app_name}.urls'.format(
            app_name=app_name,
        )
        urls_path = os.path.join(settings.BASE_DIR, urls_name.replace('.', '/') + '.py')
        if os.path.exists(urls_path):
            urls_module = import_module(urls_name)
            urls_module.urlpatterns = getattr(urls_module, 'urlpatterns', [])
            urls_module.apiurlpatterns = getattr(urls_module, 'apiurlpatterns', [])
            if hasattr(urls_module, 'viewsets'):
                urls_module.apiurlpatterns += rest_path(urls_module.viewsets)

            path_name = settings.APP_PATH[app_name]
            if urls_module.urlpatterns:
                patterns.append(
                    url(_get_sub_pattern(path_name), include(urls_module.urlpatterns, namespace=app_name))
                )

            if urls_module.apipatterns:
                apipatterns.append(
                    url(_get_sub_pattern(path_name), include(urls_module.apiurlpatterns, namespace=app_name))
                )

        app_patterns, app_apipatterns = get_app_urls(app_name)
        for sub_module_name, sub_module_patterns in app_patterns.items():
            app_sub_module_patterns.setdefault(sub_module_name, []).extend(sub_module_patterns)

        for sub_module_name, sub_module_apipatterns in app_apipatterns.items():
            app_sub_module_apipatterns.setdefault(sub_module_name, []).extend(sub_module_apipatterns)

    for sub_module_name, sub_module_patterns in app_sub_module_patterns.items():
        sub_module_path_name = settings.SUB_MODULES[sub_module_name]
        patterns.append(
            url(_get_sub_pattern(sub_module_path_name), include(sub_module_patterns, namespace=sub_module_name))
        )

    for sub_module_name, sub_module_apipatterns in app_sub_module_apipatterns.items():
        sub_module_path_name = settings.SUB_MODULES[sub_module_name]
        apipatterns.append(
            url(_get_sub_pattern(sub_module_path_name), include(sub_module_apipatterns, namespace=sub_module_name))
        )

    return patterns, apipatterns


def _get_sub_channel_pattern(routerpatterns, path_name):
    if path_name:
        return channel_include(routerpatterns, path=r'^/{path_name}'.format(path_name=path_name))
    else:
        return channel_include(routerpatterns)


def get_app_routers(app_name):
    patterns = {}
    app_path_name = settings.APP_PATH[app_name]

    for sub_module_name in settings.SUB_MODULES:
        routers_name = '{app_name}.{sub_module}.routers'.format(
            app_name=app_name,
            sub_module=sub_module_name,
        )
        routers_path = os.path.join(settings.BASE_DIR, routers_name.replace('.', '/') + '.py')
        if os.path.exists(routers_path):
            routers_module = import_module(routers_name)
            routers_module.routerpatterns = getattr(routers_module, 'routerpatterns', [])
            if hasattr(routers_module, 'websockets'):
                routers_module.routerpatterns.append(ws_path(routers_module.websockets))

            patterns.setdefault(sub_module_name, []).append(
                _get_sub_channel_pattern(routers_module.routerpatterns, app_path_name)
            )

    return patterns


def get_base_routers():
    patterns = []

    app_sub_module_patterns = {}
    for app_name in settings.APP_NAMES:
        routers_name = '{app_name}.routers'.format(
            app_name=app_name,
        )
        routers_path = os.path.join(settings.BASE_DIR, routers_name.replace('.', '/') + '.py')
        if os.path.exists(routers_path):
            routers_module = import_module(routers_path)
            routers_module.routerpatterns = getattr(routers_module, 'routerpatterns', [])
            if hasattr(routers_module, 'websockets'):
                routers_module.routerpatterns.append(ws_path(routers_module.websockets))

            path_name = settings.APP_PATH[app_name]
            patterns.append(_get_sub_channel_pattern(routers_module.routerpatterns, path_name))

        app_routerpatterns = get_app_routers(app_name)
        for sub_module_name, sub_module_routerpatterns in app_routerpatterns.items():
            app_sub_module_patterns.setdefault(sub_module_name, []).extend(sub_module_routerpatterns)

    for sub_module_name, sub_module_routerpatterns in app_sub_module_patterns.items():
        sub_module_path_name = settings.SUB_MODULES[sub_module_name]
        patterns.append(
            _get_sub_channel_pattern(sub_module_routerpatterns, sub_module_path_name)
        )

    return patterns


def load_app_settings(package):
    app_name = get_app_name(package)
    app_settings = LazyAppSettings(app_name)
    settings.MS[app_name] = app_settings
    return app_settings


def sync_init(app_name):
    app_module = import_module(app_name)
    if hasattr(app_module, 'sync_init'):
        app_module.sync_init()
    if hasattr(app_module, 'async_init'):
        async_exe(app_module.async_init)
    if hasattr(app_module, 'async_global_init'):
        async_exe_once(app_module.async_global_init)


class AppConfig(DjangoAppConfig):

    def ready(self):
        sync_init(self.name)


class LazyAppSettings(LazySettings):

    _app_name = None

    def __init__(self, app_name):
        self._app_name = app_name
        super(LazyAppSettings, self).__init__()

    def _setup(self, name=None):
        self._wrapped = AppSettings(self._app_name)

    def __setattr__(self, name, value):
        if name == '_app_name':
            self.__dict__['_app_name'] = value
        else:
            if name == '_wrapped':
                _app_name = self.__dict__.pop('_app_name', None)
                self.__dict__.clear()
                self.__dict__['_app_name'] = _app_name
            else:
                self.__dict__.pop(name, None)
            super(LazySettings, self).__setattr__(name, value)


class AppSettings(Settings):

    def __init__(self, app_name):
        app_settings_module = '{app_name}.setting'.format(
            app_name=app_name,
        )
        default_app_settings = import_module(app_settings_module)
        for setting in dir(default_app_settings):
            if setting.isupper():
                setattr(self, setting, getattr(default_app_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = app_settings_module

        self._explicit_settings = set()
        config_settings = settings.APP_SETTINGS.get(app_name)
        if config_settings:
            for setting, setting_value in config_settings.items():
                if isinstance(setting_value, dict) and hasattr(self, setting):
                    getattr(self, setting).update(setting_value)
                else:
                    setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

        if hasattr(default_app_settings, 'load_related'):
            default_app_settings.load_related(self)
