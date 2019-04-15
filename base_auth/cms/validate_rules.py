from rest_framework import exceptions
import re


def name_rules(value):
    if len(value.encode("utf-8")) < 2 or len(value.encode("utf-8")) > 20:
        raise exceptions.ValidationError({'name length is than less 1 or more 20'})


def username_rules(value):
    if not re.match(r"^[0-9a-zA-Z_]+$", value):
        raise exceptions.ValidationError({"username is invalid"})
