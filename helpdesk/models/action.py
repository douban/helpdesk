# coding: utf-8

import logging
from datetime import datetime

from helpdesk.libs.rest import DictSerializableClassMixin
from helpdesk.models.db import policy
from helpdesk.models.db.ticket import Ticket, TicketPhase
from helpdesk.config import AUTO_APPROVAL_TARGET_OBJECTS, PARAM_FILLUP, TICKET_CALLBACK_PARAMS

logger = logging.getLogger(__name__)


class Action(DictSerializableClassMixin):
    """action name, description/tips, st2 pack/action
    """
    def __init__(self, name, desc, provider_name, provider_object):
        self.name = name
        self.desc = desc
        self.target_object = provider_object
        self.provider_type = provider_name

    def __repr__(self):
        return 'Action(%s, %s, %s, %s)' % (self.name, self.desc, self.target_object, self.provider_type)

    __str__ = __repr__

    def get_action(self, provider):
        """return detailed action infos from the provider
        """
        return provider.get_action(self.target_object) or {}

    def description(self, provider):
        return self.get_action(provider).get('description')

    def params_json_schema(self, provider):
        return self.get_action(provider).get('params_json_schema')

    def parameters(self, provider, user):
        parameters = self.get_action(provider).get('parameters', {})
        for k, v in parameters.items():
            if k in TICKET_CALLBACK_PARAMS:
                parameters[k].update({"immutable": True})
            if k in PARAM_FILLUP:
                fill = PARAM_FILLUP[k]
                if callable(fill):
                    fill = fill(user)
                parameters[k].update(dict(default=fill, immutable=True))
        return parameters

    def to_dict(self, provider=None, user=None, **kw):
        action_d = super(Action, self).to_dict(**kw)
        if provider and user:
            action_d['params'] = self.parameters(provider, user)
            action = self.get_action(provider)
            action_d['params_json_schema'] = action.get('params_json_schema')
        return action_d

    async def run(self, provider, form, user):
        # too many st2 details, make this as the standard
        params = {}
        extra_params = {}
        for k, v in self.parameters(provider, user).items():
            if k in TICKET_CALLBACK_PARAMS:
                extra_params[k] = '-'
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
                    if live_value in ("true", "True", "TRUE", True):
                        live_value = True
                    else:
                        live_value = False
                params[k] = live_value

        # create ticket
        ticket = Ticket(
            title=self.name,
            provider_type=provider.provider_type,
            provider_object=self.target_object,
            params=params,
            extra_params=extra_params,
            submitter=user.name,
            reason=params.get('reason'),
            created_at=datetime.now())
        policy = await ticket.get_flow_policy()
        if not policy:
            return None, 'Failed to get ticket flow policy'

        ticket.annotate(nodes=policy.definition.get("nodes") or [])
        ticket.annotate(policy=policy.name)
        ticket.annotate(current_node=policy.init_node.get("name"))
        ticket.annotate(approval_log=list())
        ticket.annotate(approvers=await ticket.get_node_approvers(policy.init_node.get("name")))
        print(ticket)
        
        ret, msg = await ticket.pre_approve()
        if not ret:
            return None, msg
        
        id_ = await ticket.save()
        ticket_added = await Ticket.get(id_)

        if ticket_added is None:
            return ticket_added, 'Failed to create ticket.'

        if not ticket_added.is_approved:
            await ticket_added.notify(TicketPhase.REQUEST)
            return ticket_added.to_dict(), 'Success. Your request has been submitted, please wait for approval.'

        # if this ticket is auto approved, execute it immediately
        execution, _ = ticket_added.execute()
        if execution:
            await ticket_added.notify(TicketPhase.REQUEST)
        await ticket_added.save()

        return (
            ticket_added.to_dict(),
            'Success. Your request has been approved automatically, please go to ticket page for details')
    