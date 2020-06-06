# coding: utf-8

from __future__ import absolute_import

import logging
from functools import wraps

import sentry_sdk
from sentry_sdk.hub import Hub

logger = logging.getLogger(__name__)

client = sentry_sdk.Hub.current.client
if client:
    _hub = Hub(client)
else:
    _hub = None


def report(msg=None, **kw):
    if not _hub:
        return
    try:
        extra = kw.pop('extra', {})

        with sentry_sdk.push_scope() as scope:
            for k, v in extra.items():
                scope.set_extra(k, v)
            scope.level = kw.pop('level', logging.ERROR)

            if 'user' in kw:
                scope.user = kw.get('user')

            if msg:
                _hub.capture_message(msg, level=scope.level)
            else:
                _hub.capture_exception()
    except Exception:
        logger.exception('report to sentry failed: ')


def send_sentry(func):
    @wraps(func)
    def _(*a, **kw):
        try:
            return func(*a, **kw)
        except Exception:
            report()
            raise
    return _
