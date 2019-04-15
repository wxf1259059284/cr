from __future__ import unicode_literals

import ConfigParser
import contextlib
import functools
import logging
import os
import random
import re
import socket
import string
import time
import uuid


LOG = logging.getLogger(__name__)


def get_random_string(length=4,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    return ''.join(random.choice(allowed_chars) for i in range(length))


def generate_complex_str(length=12):
    complex_strs = []
    dig_len = random.randint(1, 3)
    spe_len = random.randint(1, 3)
    upp_len = random.randint(1, 3)
    low_len = length - dig_len - spe_len - upp_len

    complex_strs.extend([random.choice(string.digits)
                         for i in range(dig_len)])
    complex_strs.extend([random.choice(string.ascii_uppercase)
                         for i in range(upp_len)])
    complex_strs.extend([random.choice(string.ascii_lowercase)
                         for i in range(low_len)])

    random.shuffle(complex_strs)
    return "".join(complex_strs)


def ip_check(ip_addr):
    p = re.compile(r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$")
    return True if p.match(ip_addr) else False


def generate_uuid(dashed=True):
    if dashed:
        return str(uuid.uuid4())
    return uuid.uuid4().hex


def _format_uuid_string(string):
    return (string.replace('urn:', '')
                  .replace('uuid:', '')
                  .strip('{}')
                  .replace('-', '')
                  .lower())


def is_uuid_like(val):
    try:
        return str(uuid.UUID(val)).replace('-', '') == _format_uuid_string(val)
    except (TypeError, ValueError, AttributeError):
        return False


def getid(obj):
    try:
        return obj.id
    except AttributeError:
        return obj


class ResourceWrapper(object):
    _attrs = []
    _resource = None

    def __init__(self, resource):
        self._resource = resource

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._attrs:
                raise
            # __getattr__ won't find properties
            return getattr(self._resource, attr)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             dict((attr, getattr(self, attr))
                                  for attr in self._attrs
                                  if hasattr(self, attr)))

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._resource, key, None)
        return obj


class APIDictWrapper(object):
    """Simple wrapper for api dictionaries

    Some api calls return dictionaries.  This class provides identical
    behavior as APIResourceWrapper, except that it will also behave as a
    dictionary, in addition to attribute accesses.

    Attribute access is the preferred method of access, to be
    consistent with api resource objects from novaclient.
    """

    _apidict = {}  # Make sure _apidict is there even in __init__.

    def __init__(self, apidict):
        self._apidict = apidict

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._apidict:
                raise
            return self._apidict[attr]

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except (AttributeError, TypeError) as e:
            # caller is expecting a KeyError
            raise KeyError(e)

    def __contains__(self, item):
        try:
            return hasattr(self, item)
        except TypeError:
            return False

    def get(self, item, default=None):
        try:
            return getattr(self, item)
        except (AttributeError, TypeError):
            return default

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self._apidict)

    def to_dict(self):
        return self._apidict


class MemcacheLockException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


@contextlib.contextmanager
def memcache_lock(mc, key, attempts=600, expires=120):
    key = '__oj_lock_%s' % key

    got_lock = False
    try:
        got_lock = _acquire_lock(mc, key, attempts, expires)
        yield
    finally:
        if got_lock:
            _release_lock(mc, key)


def _acquire_lock(mc, key, attempts, expires):
    for i in range(0, attempts):
        stored = mc.add(key, 1, expires)
        if stored:
            return True
        if i != attempts-1:
            sleep_time = random.randint(1, 10)/10.0
            logging.debug('Sleeping for %ss while '
                          'trying to acquire key %s', sleep_time, key)
            time.sleep(sleep_time)
    raise MemcacheLockException('Could not acquire lock for %s' % key)


def _release_lock(mc, key):
    mc.delete(key)


def get_local_hostname():
    try:
        return socket.gethostname()
    except Exception as e:
        LOG.error("Unable to get local hostname")
        LOG.error(e)
    return None


def get_ip_by_hostname(hostname):
    try:
        return socket.gethostbyname(hostname)
    except Exception as e:
        LOG.error("Unable to get ip by hostname {}".format(hostname))
        LOG.error(e)
    return None


def to_dict(_resource, _attrs):
    obj = {}
    for key in _attrs:
        obj[key] = getattr(_resource, key, None)
    return obj


class LazyLoader(object):
    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.args = args
        self.kwargs = kwargs
        self.instance = None

    def __getattr__(self, name):
        return functools.partial(self.__run_method, name)

    def __run_method(self, __name, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*self.args, **self.kwargs)
        return getattr(self.instance, __name)(*args, **kwargs)


def get_nova_config(section, option, conf_file=None):
    if not conf_file:
        conf_file = "/etc/nova/nova.conf"
    if not os.path.isfile(conf_file):
        return None

    cp = ConfigParser.ConfigParser()
    cp.read(conf_file)
    try:
        return cp.get(section=section, option=option)
    except Exception:
        return None


def nova_instance_dir():
    inst_path = get_nova_config("DEFAULT", "instances_path")
    if not inst_path:
        state_path = get_nova_config("DEFAULT", "state_path")
        if state_path:
            inst_path = os.path.join(state_path, "instances")
        else:
            inst_path = "/var/lib/nova/instances"
    if not os.path.exists(inst_path):
        return None
    return inst_path


def glance_image_dir():
    image_path = get_nova_config("glance_store", "filesystem_store_datadir",
                                 conf_file="/etc/glance/glance-api.conf")
    if not image_path:
        image_path = "/var/lib/glance/images"
    if not os.path.exists(image_path):
        return None
    return image_path


def logger_decorator(logger):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            func_name = func.__name__
            logger.debug("[OPENSTACK] Start {}(): args={}, "
                         "kwargs={}".format(func_name, args, kwargs))
            ff = func(self, *args, **kwargs)
            logger.debug("[OPENSTACK] End {}()".format(func_name))
            return ff
        return wrapper
    return decorator


def handle_error(logger, err_msg=None, e=None):
    if not err_msg:
        err_msg = "Unknown error occurred, Please try again later."
    if e:
        err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
    logger.error("[OPENSTACK] {}".format(err_msg))
    raise Exception(err_msg)
