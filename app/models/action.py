# coding: utf-8

import logging
from datetime import datetime

from app.models.db.ticket import Ticket
from app.config import AUTO_APPROVAL_TARGET_OBJECTS

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

    async def run(self, provider, form):
        # NOTE: too many st2 details, maybe make this as the standard
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

        ticket = Ticket(provider_type=provider.provider_type,
                        provider_object=self.target_object,
                        params=params,
                        submitter=provider.user,
                        reason=params.get('reason'),
                        created_at=datetime.now())

        if self.target_object in AUTO_APPROVAL_TARGET_OBJECTS:
            ticket.approve(auto=True)

        id_ = await ticket.save()
        ticket_added = await Ticket.get(id_)

        if ticket_added is None:
            return ticket_added, 'Failed to create ticket.'

        if not ticket.is_approved:
            return ticket_added.to_dict(), 'Success. Your request has been submitted, please wait for approval.'

        logger.info('run action %s, params: %s', self.target_object, params)
        execution, msg = provider.run_action(self.target_object, params)
        if not execution:
            return execution, msg

        ticket.executed_at = datetime.now()
        ticket.save()
        return execution, 'Success. <a href="%s" target="_blank">result</a>' % (execution['web_url'],)
