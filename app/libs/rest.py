# -*- coding: utf-8 -*-

import re
import logging
import asyncio
from functools import wraps
from datetime import datetime
from collections import Iterable

from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def jsonize(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def _(*args, **kwargs):
            ret = await func(*args, **kwargs)
            data = json_unpack(ret)
            # logger.debug('jsonize: args: %s, kwargs: %s, ret: %s, data: %s', args, kwargs, ret, data)
            status_code = data.get('status_code') if data and isinstance(data, dict) else None
            return JSONResponse(dict(data=data), status_code=status_code or 200)
        return _
    else:
        @wraps(func)
        def _(*args, **kwargs):
            ret = func(*args, **kwargs)
            data = json_unpack(ret)
            # logger.debug('jsonize: args: %s, kwargs: %s, ret: %s, data: %s', args, kwargs, ret, data)
            status_code = data.get('status_code') if data and isinstance(data, dict) else None
            return JSONResponse(dict(data=data), status_code=status_code or 200)
        return _


class DictSerializableClassMixin(object):
    def to_dict(self, show=None, **kw):
        return json_unpack(self)


def dictify(obj):
    """turn an object to a dict, return None if can't"""
    d = None
    if hasattr(obj, '__dict__') and obj.__dict__:
        d = obj.__dict__
        if not isinstance(d, dict):
            d = dict(d)

        # deal with properties
        if hasattr(obj, '__class__'):
            properties = {}
            for cls_attr in dir(obj.__class__):
                if cls_attr.startswith('_'):
                    continue
                attr = getattr(obj.__class__, cls_attr)
                if isinstance(attr, property):
                    try:
                        properties[cls_attr] = attr.__get__(obj, obj.__class__)
                    except Exception:
                        properties[cls_attr] = ''
            d.update(properties)
    return d


def isa_json_primitive_type(obj):
    return isinstance(obj, (int, str))


def json_unpack(obj, visited=None):
    """unpack an object to a jsonable form, return None if can't"""
    if visited is None:
        visited = {}
    if isa_json_primitive_type(obj):
        return obj
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, dict):
        return {k: json_unpack(v, visited) for k, v in obj.items()}
    elif isinstance(obj, Iterable):
        return [json_unpack(v, visited) for v in obj]
    d = dictify(obj)
    visited[id(obj)] = True
    return ({k: json_unpack(v, visited)
             for k, v in d.items() if id(v) not in visited and not k.startswith('_')}
            if d is not None else None)


class ApiError(Exception):
    def __init__(self, error, description=""):
        error_code, message, status_code = error
        self.error_code = error_code
        self.status_code = status_code
        self.message = message
        self.description = description

    def __str__(self):
        return '[{message}] {description}'.format(**self.to_dict())

    __repr__ = __str__

    def to_dict(self):
        return {
            'error_code': self.error_code,
            'status_code': self.status_code,
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


def yaml_validator(s):
    import yaml
    try:
        yaml.safe_load(s)
        return True
    except yaml.YAMLError as e:
        logger.info('failed validate yaml: %s: %s', s, str(e))


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
