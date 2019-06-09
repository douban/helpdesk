# coding: utf-8

import logging
from datetime import datetime

from app.libs.rest import DictSerializableClassMixin
from app.models.db.ticket import Ticket
from app.config import AUTO_APPROVAL_TARGET_OBJECTS, PARAM_FILLUP

logger = logging.getLogger(__name__)


class Action(DictSerializableClassMixin):
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
        parameters = self.get_action(provider).get('parameters', {})
        for k, v in parameters.items():
            if k in PARAM_FILLUP:
                fill = PARAM_FILLUP[k]
                if callable(fill):
                    fill = fill(provider)
                parameters[k].update(dict(default=fill, immutable=True))
        return parameters

    async def run(self, provider, form, is_admin=False):
        # too many st2 details, make this as the standard
        params = {}
        for k, v in self.parameters(provider).items():
            if k in PARAM_FILLUP:
                logger.debug('filling up parameter: %s, by value: %s', k, v['default'])
                params[k] = v['default']
                continue
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
                if v.get('type') == 'boolean':
                    live_value = True
                params[k] = live_value

        # create ticket
        ticket = Ticket(title=self.name,
                        provider_type=provider.provider_type,
                        provider_object=self.target_object,
                        params=params,
                        submitter=provider.user,
                        reason=params.get('reason'),
                        created_at=datetime.now())

        # if auto pass
        if self.target_object in AUTO_APPROVAL_TARGET_OBJECTS or is_admin:
            ret, msg = ticket.approve(auto=True)
            if not ret:
                return None, msg

        id_ = await ticket.save()
        ticket_added = await Ticket.get(id_)

        if ticket_added is None:
            return ticket_added, 'Failed to create ticket.'

        if not ticket_added.is_approved:
            ticket_added.notify('request')
            return ticket_added.to_dict(), 'Success. Your request has been submitted, please wait for approval.'

        # if this ticket is auto approved, execute it immediately
        execution, msg = ticket_added.execute(provider=provider, is_admin=is_admin)
        if execution:
            await ticket_added.save()
            ticket_added.notify('request')

        return execution, msg
