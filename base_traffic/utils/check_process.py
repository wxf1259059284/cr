# -*- coding: utf-8 -*-
import os


def check_process(pid=None):
    if pid is None:
        return {'status': 'ok', 'alive': False}
    try:
        os.kill(pid, 0)
    except OSError:
        return {'status': 'ok', 'alive': False}
    else:
        return {'status': 'down', 'alive': True}
