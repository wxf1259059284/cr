# -*- coding: utf-8 -*-
import re


# 去除docker不允许的非法字符
def str_filter(resource_str):
    char_p = re.compile(r'[^a-zA-Z0-9_.-]')
    converted_str, count = char_p.subn('', resource_str)
    illegal_start_p = re.compile(r'^[_.-][a-zA-Z0-9_.-]+')
    if illegal_start_p.match(converted_str):
        converted_str = 'D%s' % converted_str
    return converted_str
