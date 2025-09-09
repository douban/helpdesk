# coding: utf-8

import logging
from datetime import datetime
from typing import Dict, Any

from helpdesk.libs.decorators import timed_cache
from helpdesk.libs.preprocess import get_preprocess
from helpdesk.libs.rest import DictSerializableClassMixin
from helpdesk.libs.types import ActionSchema
from helpdesk.models.db.ticket import Ticket, TicketPhase
from helpdesk.config import PARAM_FILLUP, TICKET_CALLBACK_PARAMS, PREPROCESS_TICKET
from helpdesk.views.api.schemas import ApproverType
from helpdesk.models.provider.base import BaseProvider

logger = logging.getLogger(__name__)


class ActionResolveError(Exception):
    pass


class Action(DictSerializableClassMixin):
    """action name, description/tips
    """
    def __init__(self, name: str, desc: str, provider_type: str, target_object: str):
        self.name = name
        self.desc = desc
        self.target_object = target_object
        self.provider_type = provider_type

    def __repr__(self):
        return 'Action(%s, %s, %s, %s)' % (self.name, self.desc, self.target_object, self.provider_type)

    __str__ = __repr__

    @timed_cache(seconds=60)
    def resolve_action(self, provider: BaseProvider) -> ActionSchema:
        """
        return detailed action infos from the provider
        """
        action_info = provider.get_action_schema(self.target_object)
        if not action_info:
            raise ActionResolveError(f"resolve action {self.target_object} failed")
        return action_info

    def description(self, provider):
        return self.resolve_action(provider).description

    def params_json_schema(self, provider):
        return self.resolve_action(provider).params_json_schema

    def parameters(self, provider: BaseProvider, user) -> Dict[str, Any]:
        parameters = self.resolve_action(provider).parameters
        for k in parameters:
            if k in TICKET_CALLBACK_PARAMS:
                parameters[k].immutable = True
            if k in PARAM_FILLUP:
                fill = PARAM_FILLUP[k]
                if callable(fill):
                    fill = fill(user)
                parameters[k].default = fill
                parameters[k].immutable = True
        return {k:v.dict() for k, v in parameters.items()}

    def to_dict(self, provider=None, user=None, **kw):
        action_d = super(Action, self).to_dict(**kw)
        if provider and user:
            action_d['params'] = self.parameters(provider, user)
            action = self.resolve_action(provider)
            action_d['params_json_schema'] = action.params_json_schema
        return action_d

    async def run(self, provider, form, user):
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

        # 参数预处理
        for preprocess_info in PREPROCESS_TICKET:
            if self.target_object in preprocess_info["actions"]:
                params_pre = get_preprocess(preprocess_info["type"])
                success, params = await params_pre.process(params)
                if not success:
                    return None, 'Failed to preprocess the params, please check ticket params'
        # create ticket
        ticket = Ticket(
            title=self.name,
            provider_type=provider.provider_type,
            provider_object=self.target_object,
            params=params,
            extra_params=extra_params,
            submitter=user.name,
            reason=params.get('reason'),
            created_at=datetime.now()
        )
        policy = await ticket.get_flow_policy()
        if not policy:
            return None, 'Failed to get ticket flow policy'

        ticket.annotate(nodes=policy.definition.get("nodes") or [])
        ticket.annotate(policy=policy.name)
        ticket.annotate(approval_log=list())
        current_node = ticket.init_node
        ticket.annotate(current_node=current_node.get("name"))
        approvers = await ticket.get_node_approvers(current_node.get("name"))
        if not approvers and current_node.get("approver_type") == ApproverType.APP_OWNER:
            return None, "Failed to get app approvers, please confirm that the app name is entered correctly"
        ticket.annotate(approvers=approvers)

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
