# coding: utf-8


class Provider:
    def __init__(self):
        pass

    def get_actions(self, pack=None):
        '''
        return a list of action dict
        '''
        pass

    # TODO: cache ttl
    def get_action(self, ref):
        pass


def get_provider(provider):
    from app.models.providers.st2 import ST2Provider

    return {'st2': ST2Provider}[provider]()
