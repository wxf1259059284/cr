# -*- coding: utf-8 -*-
from channels import Channel


def start_checker(data, logger, no_delay=False):
    """
    start check function(Self-start)
    :param data:
    :param logger:
    :param no_delay:no_delay==True:立即执行
    :return:
    """

    if no_delay:
        first_check_time = 0
    else:
        first_check_time = data.get("first_check_time", 0) * 1000

    logger.info("Check time : %s", first_check_time)

    delayed_message = {
        'channel': 'control',
        'content': data,
        'delay': first_check_time
    }
    Channel('asgi.delay').send(delayed_message)
