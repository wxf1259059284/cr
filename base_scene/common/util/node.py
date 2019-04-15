# -*- coding: utf-8 -*-
from base.utils.functional import cached_property
from base_proxy import app_settings as proxy_settings


class NodeUtil(object):
    def __init__(self, node):
        self.node = node

    def __call__(self, user=None, remote=True, proxy=False):
        self.user = user
        self.remote = remote
        self.proxy = proxy and proxy_settings.SWITCH
        return self

    def update_node(self, params, save=True):
        self.node.__dict__.update(params)
        if save:
            self.node.__class__.objects.filter(pk=self.node.pk).update(**params)

    def refresh_node(self):
        self.node = self.node.__class__.objects.get(pk=self.node.pk)

    @cached_property
    def scene(self):
        return self.node.scene

    @cached_property
    def scene_util(self):
        from .scene import SceneUtil
        return SceneUtil(self.scene)
