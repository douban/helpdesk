# coding: utf-8

import logging

logger = logging.getLogger(__name__)


class Action:
    """action name, description/tips, st2 pack/action
    """
    def __init__(self, name, desc, provider_object):
        self.name = name
        self.desc = desc
        self.target_object = provider_object

    def __repr__(self):
        return 'Action(%s, %s, %s)' % (self.name, self.desc, self.target_object)

    __str__ = __repr__

    def get_action(self, provider):
        """return detailed action infos from the provider
        """
        return provider.get_action(self.target_object) or {}

    def description(self, provider):
        return self.get_action(provider).get('description')

    def parameters(self, provider):
        return self.get_action(provider).get('parameters', {})

    def run(self, provider, form):

        # FIXME: too many st2 details
        params = {}
        for k, v in self.parameters(provider).items():
            live_value = form.get(k)
            logger.debug('k: %s, v: %s, live_value: %s', k, v, live_value)
            if v.get('immutable'):
                if live_value is not None:
                    logger.warn('get a value for an immutable parameter, ignoring.')
                continue
            if v.get('required') and v.get('default') is None and not live_value:
                msg = 'miss a value for a required parameter, aborting.'
                logger.error(msg)
                return None, msg
            if live_value is not None:
                # TODO: validate type
                if v.get('type') == 'boolean' and live_value == 'on':
                    live_value = True
                params[k] = live_value

        logger.info('run action %s, params: %s', self.target_object, params)
        execution = provider.run_action(self.target_object, params)
        return execution, 'success, <a href="%s" target="_blank">result</a>' % (execution['web_url'],)
