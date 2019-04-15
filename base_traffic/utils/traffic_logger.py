# -*- coding: utf-8 -*-
import hashlib
import logging

import os

import sys

from cr import settings
from cr_scene.utils.uitls import get_cr_scene_name


def scene_log_key(key, name):
    _key = hashlib.md5('{}-scene-traffic'.format(key)).hexdigest()
    return _key


class TrafficLogFactory(object):
    logger_pool = {}

    def __new__(cls, scene_id, name):

        cr_scene_name = get_cr_scene_name(scene_id)
        _key = scene_log_key(cr_scene_name, name)

        if _key in cls.logger_pool:
            _logger = cls.logger_pool[_key]
        else:
            _logger = cls._generate(_key, cr_scene_name)
            cls.logger_pool[_key] = _logger
        return _logger

    @classmethod
    def _generate(cls, key, name):

        logger = logging.getLogger(key)

        # 指定logger输出格式
        formatter = logging.Formatter('%(levelname)s %(asctime)s %(module)s - %(message)s')

        # 文件日志
        file_handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'log/scene-{}-traffic.log'.format(name)))
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
#
#     @classmethod
#     def destroy(cls, event_id, name):
#
#         _key = scene_log_key(event_id, name)
#
#         if _key in cls.logger_pool:
#             logger = cls.logger_pool[_key]
#             logging.Logger.manager.loggerDict.pop(_key)
#             logger.manager = None
#             logger.handlers = []
#             cls.logger_pool.pop(_key)
#
#
# def get_scene_logger(event_id, name):
#     logger = SceneLogFactory(event_id, name)
#     return logger
