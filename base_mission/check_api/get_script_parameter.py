# -*- coding: utf-8 -*-
from base_mission.check_api.parameter_validation import ip_verification
import json
import ast


def kwargs_process(data, kwargs):
    """
    Combine kwargs and data,
    the same parameters are in data,
    and other parameters are in data["kwargs"]
    :param data:
    :param kwargs:
    :return:
    """
    if kwargs:
        try:
            kwargs = ast.literal_eval(kwargs)
            if type(kwargs) != dict:
                kwargs = kwargs_conversion(kwargs)
        except Exception:
            kwargs = kwargs_conversion(kwargs)

        if kwargs.get("checker_ip"):
            kwargs.pop("checker_ip")
        elif kwargs.values()[0]:
            if ip_verification(kwargs.values()[0]):
                kwargs.pop(kwargs.keys()[0])

        data["kwargs"] = kwargs

    return data


def kwargs_conversion(kwargs):
    new_kwargs = {}
    try:
        if type(str(kwargs)) == str:
            kwargs = str(kwargs)
            if "," in kwargs:
                kwargs = kwargs.split(",")
                for elements in kwargs:
                    if "=" in elements:
                        element = elements.split("=")
                        if len(element) == 2:
                            key = element[0].strip()
                            new_kwargs[key] = json.loads(element[1])
                    else:
                        new_kwargs["params"] = " ".join(kwargs)
                        return new_kwargs
            else:
                new_kwargs["params"] = kwargs
    except Exception:
        if type(kwargs) == dict:
            new_kwargs = ast.literal_eval(kwargs)
        else:
            new_kwargs = {}

    return new_kwargs
