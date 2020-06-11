# coding: utf-8

from datetime import datetime


class BaseProvider:
    provider_type = ''

    def __init__(self, **kwargs):
        pass

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
