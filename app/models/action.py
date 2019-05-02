# coding: utf-8

import logging

from app.config import PROVIDER
from app.models.provider import get_provider

logger = logging.getLogger(__name__)


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

    def run(self, form):

        # FIXME: too many st2 details
        params = {}
        for k, v in self.parameters.items():
            live_value = form.get(k)
            logger.debug('k: %s, v: %s, live_value: %s', k, v, live_value)
            if v.get('immutable'):
                if live_value is not None:
                    logger.warn('get a value for an immutable parameter, ignoring.')
                continue
            if v.get('required') and v.get('default') is None and live_value is None:
                msg = 'miss a value for a required parameter, aborting.'
                logger.error(msg)
                return None, msg
            if live_value is not None:
                # TODO: validate type
                params[k] = live_value

        logger.info('run action %s, params: %s', self.target_object, params)
        execution = self.provider.run_action(self.target_object, params)
        return execution, 'success, %s' % (execution['web_url'],)
