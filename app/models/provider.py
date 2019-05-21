# coding: utf-8


class Provider:
    provider_type = ''

    def __init__(self, token=None, user=None, **kw):
        self.token = token
        self.user = user

    def get_actions(self, pack=None):
        '''
        return a list of action dict
        '''
        pass

    # TODO: cache result, ttl
    def get_action(self, ref):
        pass

    def run_action(self, ref, parameters):
        pass

    def authenticate(self, user, password):
        pass


# TODO: cache in pool by kw, ttl
def get_provider(provider, **kw):
    from app.models.providers.st2 import ST2Provider

    return {'st2': ST2Provider}[provider](**kw)
