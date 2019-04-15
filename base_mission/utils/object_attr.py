# -*- coding: utf-8 -*-
def object_attr(obj, attr):
    """
    Take the required attributes from the object
    :param obj: object
    :param attr: attributes name
    :return: attr or None
    """
    if hasattr(obj, attr):
        return getattr(obj, attr)
    else:
        return None
