import time

from base.utils.functional import cached_property
from base.utils.cache import CacheProduct

from base_scene import app_settings


class DockerLockException(Exception):
    pass


class DockerCreateLock(object):

    def __init__(self, scene_terminal, timeout=app_settings.MAX_DOCKER_BLOCK_SECONDS, key_prefix=None,
                 extra_cidrs=None):
        cidrs = []
        for net in scene_terminal.nets.all():
            if net.cidr:
                cidrs.append(net.cidr)
            elif net.sub_id.lower().startswith(app_settings.EXTERNAL_NET_ID_PREFIX):
                cidrs.append(app_settings.EXTERNAL_NET_ID_PREFIX)

        if extra_cidrs:
            cidrs.extend(extra_cidrs)
        self.cidrs = cidrs
        self.key_prefix = key_prefix or ''
        self.timeout = timeout

        self._locked_cidrs = []

    def __enter__(self):
        self.get_locks()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_locks()

    @cached_property
    def cache(self):
        cls = self.__class__
        return CacheProduct('{}.{}'.format(cls.__module__, cls.__name__))

    def gkey(self, cidr):
        return 'docker_lock:{key_prefix}:{cidr}'.format(
            key_prefix=self.key_prefix,
            cidr=cidr,
        )

    def get_lock(self, cidr):
        key = self.gkey(cidr)
        result = self.cache.add(key, 1, self.timeout)
        if result:
            self._locked_cidrs.append(cidr)

        return result

    def release_lock(self, cidr):
        key = self.gkey(cidr)
        self.cache.delete(key)
        self._locked_cidrs.remove(cidr)

    def get_locks(self):
        for cidr in self.cidrs:
            if not self.get_lock(cidr):
                raise DockerLockException()

    def release_locks(self):
        for cidr in self._locked_cidrs:
            self.release_lock(cidr)


class CreateDockerLock(object):

    def __init__(self, scene_terminal, block=2):
        self.d_lock = DockerCreateLock(scene_terminal)
        self.block = block
        self.time = (app_settings.MAX_DOCKER_BLOCK_SECONDS / block) or 1

    def __enter__(self):
        for i in xrange(self.time):
            try:
                self.d_lock.get_locks()
            except DockerLockException:
                self.d_lock.release_locks()
                time.sleep(self.block)
            else:
                break

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.d_lock.release_locks()


create_docker_lock = CreateDockerLock
