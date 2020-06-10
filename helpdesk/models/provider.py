# coding: utf-8

from datetime import datetime

from starlette.authentication import has_required_scope

from helpdesk.libs.decorators import timed_cache


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

    def get_default_pack(self):
        raise NotImplementedError()

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

    def get_execution(self, execution_id):
        raise NotImplementedError()

    def get_execution_output(self, execution_output_id):
        return self.get_execution(execution_output_id)


@timed_cache(minutes=15)
def get_provider(provider, **kw):
    from helpdesk.models.providers.st2 import ST2Provider
    from helpdesk.models.providers.airflow import AirflowProvider
    from helpdesk.models.providers.spincycle import SpinCycleProvider

    return {'st2': ST2Provider, 'airflow': AirflowProvider, 'spincycle': SpinCycleProvider}[provider](**kw)


def get_provider_by_action_auth(request, action):
    if not has_required_scope(request, ['authenticated']):
        return None
    return get_provider(action.provider_type)
