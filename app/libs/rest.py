# -*- coding: utf-8 -*-

import re
from functools import wraps
from datetime import datetime
from collections import Iterable

from starlette.responses import JSONResponse


def jsonize(func):
    @wraps(func)
    def _(*args, **kwargs):
        ret = func(*args, **kwargs)
        data = json_unpack(ret)

        return JSONResponse(dict(data=data))
    return _


def dictify(obj):
    """turn an object to a dict, return None if can't"""
    d = None
    if d is None and hasattr(obj, '__dict__') and obj.__dict__:
        d = obj.__dict__
    return d


def isa_json_primitive_type(obj):
    return isinstance(obj, (int, str))


def json_unpack(obj, visited=None):
    """unpack an object to a jsonable form, return None if can't"""
    if visited is None:
        visited = {}
    visited[id(obj)] = True
    if isa_json_primitive_type(obj):
        return obj
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, dict):
        return {k: json_unpack(v, visited) for k, v in obj.items()}
    elif isinstance(obj, Iterable):
        return [json_unpack(v, visited) for v in obj]
    d = dictify(obj)
    return ({k: json_unpack(v, visited)
             for k, v in d.items() if id(v) not in visited and not k.startswith('_')}
            if d is not None else None)


class ApiError(Exception):
    def __init__(self, error, description=""):
        code, message, status = error
        self.code = code
        self.status = status
        self.message = message
        self.description = description

    def __str__(self):
        return '[{message}] {description}'.format(**self.to_dict())

    __repr__ = __str__

    def to_dict(self):
        return {
            'code': self.code,
            'status': self.status,
            'message': self.message,
            'description': self.description,
        }


class ApiErrors(object):
    """built-in Api Errors"""
    parameter_required = (10001, 'parameter_required', 400)
    parameter_type_mismatch = (10002, 'parameter_type_mismatch', 400)
    parameter_validation_failed = (10003, 'parameter_validation_failed', 400)


RE_PATTERN_IPADDRESS = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")  # NOQA
RE_PATTERN_IPADDRESS_OR_SECTION = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])?$")  # NOQA


def ip_address_or_section_validator(ip):
    return bool(RE_PATTERN_IPADDRESS_OR_SECTION.match(ip))


def ip_address_validator(ip):
    return bool(RE_PATTERN_IPADDRESS.match(ip))


def check_parameter(params, name, type_, validator=None, optional=False, default=None):
    """`type_` should be a class, such as int, str..."""
    value = params.get(name)
    if value is None:
        if default is not None:
            return default
        if not optional:
            raise ApiError(ApiErrors.parameter_required,
                           'parameter `{name}` is required'.format(name=name))
        return None
    if not isinstance(value, type_):
        try:
            value = type_(value)
        except Exception:
            raise ApiError(ApiErrors.parameter_type_mismatch,
                           'parameter `{name}` type mismatch'.format(name=name))
    if validator and not validator(value):
        raise ApiError(ApiErrors.parameter_validation_failed,
                       'parameter `{name}` validation failed'.format(name=name))
    return value
