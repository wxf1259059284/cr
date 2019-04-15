# -*- coding: utf-8 -*-
from base_mission.utils.type_judgement import type_judgement
from base_mission.utils.object_attr import object_attr
import re


def parameter_verification(data, parameter_list):
    """
    :param data: Data to be validated
    :param parameter_list: Fields to be validated, Iterative object
    :return: dict
    """
    # if not isinstance(parameter_list, Iterable):
    #     return {}
    if not type_judgement(parameter_list, list):
        return {}

    if isinstance(data, dict):
        parameter_dict = dict_data(data, parameter_list)
    else:
        parameter_dict = obj_data(data, parameter_list)

    return parameter_dict


def dict_data(data, parameter_list):
    if not type_judgement(data, dict):
        return {}

    parameter_dict = {}
    for parameter in parameter_list:
        parameter_value = data.get(parameter, None)
        if parameter_value is not None:
            parameter_dict.update({
                parameter: parameter_value
            })
        else:
            return {}
    return parameter_dict


def obj_data(obj, parameter_list):
    parameter_dict = {}
    for parameter in parameter_list:
        parameter_value = object_attr(obj, parameter)

        if parameter_value is not None:
            parameter_dict.update({
                parameter: parameter_value
            })
        else:
            return {}
    return parameter_dict


def ip_verification(ip):
    pat = re.compile(r'([0-9]{1,3})\.')
    try:
        r = re.findall(pat, ip + ".")
        if len(r) == 4 and len([x for x in r if 0 <= int(x) <= 255]) == 4:
            return True
        else:
            return False
    except Exception:
        return False
