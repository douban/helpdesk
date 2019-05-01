# coding: utf-8

from app.config import PROVIDER
from app.models.provider import get_provider


class Action:
    """action name, description/tips, st2 pack/action
    """
    def __init__(self, name, desc, provider_object):
        self.name = name
        self.desc = desc
        self.target_object = provider_object

        self.provider = get_provider(PROVIDER)

    def __repr__(self):
        return 'Action(%s, %s, %s)' % (self.name, self.desc, self.target_object)

    __str__ = __repr__

    def get_action(self):
        '''
        return detailed action infos from the provider
        '''
        return self.provider.get_action(self.target_object) or {}

    @property
    def description(self):
        return self.get_action().get('description')

    @property
    def parameters(self):
        return self.get_action().get('parameters', {})
