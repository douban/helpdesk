# coding: utf-8


class Provider:
    def __init__(self, token=None, **kw):
        self.token = token

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
