# coding: utf-8

from datetime import datetime


class Provider:
    provider_type = ''

    def __init__(self, token=None, user=None, **kw):
        self.token = token
        self.user = user

    def __str__(self):
        attrs = []
        for k in sorted(self.__dict__):
            if k.startswith('_'):
                continue
            v = getattr(self, k)
            v = '"%s"' % str(v) if type(v) in (str, datetime) else str(v)
            attrs.append('%s=%s' % (k, v))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(attrs))

    __repr__ = __str__

    def get_actions(self, pack=None):
        '''
        return a list of action dict,
        should follow st2 specs.
        '''
        raise NotImplementedError()

    # TODO: cache result, ttl
    def get_action(self, ref):
        raise NotImplementedError()

    def run_action(self, ref, parameters):
        raise NotImplementedError()

    def authenticate(self, user, password):
        raise NotImplementedError()

    def get_user_roles(self, user=None):
        '''return a list of roles,
            e.g. ["admin"]
        '''
        raise NotImplementedError()

    def get_user_email(self, user=None):
        raise NotImplementedError()


# TODO: cache in pool by kw, ttl
def get_provider(provider, **kw):
    from app.models.providers.st2 import ST2Provider

    return {'st2': ST2Provider}[provider](**kw)
