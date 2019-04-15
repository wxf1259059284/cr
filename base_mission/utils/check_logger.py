# -*- coding: utf-8 -*-
import hashlib
import logging

import os

import sys

from cr_scene.utils.uitls import get_cr_scene_name
from cr import settings


def scene_log_key(scene_name, name):
    _key = hashlib.md5('{}-scene'.format(scene_name)).hexdigest()
    return _key


class SceneLogFactory(object):
    logger_pool = {}

    def __new__(cls, scene_id, name):

        scene_name = get_cr_scene_name(scene_id)

        _key = scene_log_key(scene_name, name)

        if _key in cls.logger_pool:
            _logger = cls.logger_pool[_key]
        else:
            _logger = cls._generate(_key, scene_name)
            cls.logger_pool[_key] = _logger
        return _logger

    @classmethod
    def _generate(cls, key, scene_name):

        logger = logging.getLogger(key)

        # 指定logger输出格式
        # formatter = logging.Formatter('%(levelname)s %(asctime)s %(module)s - %(message)s')
        formatter = logging.Formatter('%(levelname)s %(asctime)s - %(message)s')

        # 文件日志
        file_handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'log/scene-{}.log'.format(scene_name)))
        file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式

        # 控制台日志
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = formatter  # 也可以直接给formatter赋值

        # 为logger添加的日志处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.setLevel(logging.INFO)
        logger.propagate = 0
        return logger
