# coding: utf-8

import logging
import importlib
from enum import Enum
from datetime import datetime
from urllib.parse import urlencode, quote_plus
from authlib.jose import jwt
from sqlalchemy.sql.expression import and_
from helpdesk.libs.approver_provider import get_approver_provider

from helpdesk.libs.decorators import cached_property
from helpdesk.libs.sentry import report
from helpdesk.models import db
from helpdesk.models.db.param_rule import ParamRule
from helpdesk.models.db.policy import Policy
from helpdesk.models.db.policy import TicketPolicy
from helpdesk.models.provider import get_provider
from helpdesk.config import (
    SYSTEM_USER,
    SESSION_SECRET_KEY,
    DEFAULT_BASE_URL,
    TICKET_CALLBACK_PARAMS,
    NOTIFICATION_METHODS,
)
from helpdesk.views.api.schemas import ApproverType, NodeType

logger = logging.getLogger(__name__)

TICKET_COLORS = {
    'approved': '#28a745',
    'rejected': '#dc3545',
    'pending': '#ffc107',
    'failed': '#dc3545',
    'complete': '#28a745',
    'running': '#ffc107',
    'success': '#28a745',
    'submitted': '#007bff',
    'submit_error': '#dc3545',
    'succeeded': '#28a745',
    'closed': '#28a745',
}


class TicketPhase(Enum):
    APPROVAL = 'approval'
    MARK = 'mark'
    REQUEST = 'request'


class Ticket(db.Model):
    __tablename__ = 'ticket'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=64))
    provider_type = db.Column(db.String(length=16))
    provider_object = db.Column(db.String(length=64))
    params = db.Column(db.JSON)
    extra_params = db.Column(db.JSON)
    submitter = db.Column(db.String(length=32), index=True)
    cc = db.Column(db.String(length=64))
    reason = db.Column(db.String(length=128))

    # is_approved default is None, it will become True when approved,
    #   become False when rejected
    is_approved = db.Column(db.Boolean)
    confirmed_by = db.Column(db.String(length=32))
    confirmed_at = db.Column(db.DateTime)

    # TODO: if this provider_object is bound to an approver rule
    #   then do the rule and store the state to the annotation

    annotation = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
    executed_at = db.Column(db.DateTime)

    @classmethod
    async def get_all_by_submitter(cls, submitter, desc=False, limit=None, offset=None, filter_=None, **kw):
        submitter_filter = cls.__table__.c.submitter == submitter
        if filter_ is not None:
            filter_ = and_(filter_, submitter_filter)
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset, **kw)

    @classmethod
    async def count_by_submitter(cls, submitter, filter_=None):
        submitter_filter = cls.__table__.c.submitter == submitter
        if filter_ is not None:
            filter_ = and_(filter_, submitter_filter)
        return await cls.count(filter_=filter_)

    @property
    def status(self):
        """
        created -> pending -> rejected/approved -> submitted/submit_error -> running -> succeed/failed/unknown
        当用户操作关闭后出现的工单状态 - closed
        :return:
        """
        annotation = self.annotation if self.annotation else {}
        execution_status = annotation.get('execution_status')
        execution_submitted = annotation.get('execution_submitted')
        execution_create_success = annotation.get('execution_creation_success')
        ticket_close = annotation.get('closed') or False
        if ticket_close:
            return 'closed'
        if execution_status:
            return execution_status
        elif execution_submitted:
            if execution_create_success:
                return 'submitted'
            else:
                return 'submit_error'
        elif self.is_approved is None:
            return 'pending'
        elif self.is_approved in (True, False):
            return ['rejected', 'approved'][self.is_approved]
        else:
            return 'created'

    @property
    def color(self):
        return TICKET_COLORS.get(self.status.lower(), '#6c757d')

    @property
    def ccs(self):
        return self.cc.split(',') if self.cc else []

    @property
    def display_params(self):
        if not self.params:
            return None
        return '; '.join(['%s: %s' % (k, v) for k, v in self.params.items() if k not in ('reason',)])

    async def can_view(self, user):
        return (
            user.is_admin or user.name == self.submitter or user.name in self.ccs or
            user.name in await self.all_flow_approvers())

    async def can_admin(self, user):
        approvers = await self.get_node_approvers(self.annotation.get("current_node"))
        return user.is_admin or user.name in approvers

    @cached_property
    async def rules(self):
        # param rules
        rules = await ParamRule.get_all_by_provider_object(self.provider_object)
        return [rule for rule in rules if rule.match(self.params)]

    async def get_rule_actions(self, rule_action):
        assert rule_action in ('is_auto_approval', 'approver')
        ret = filter(None, [getattr(r, rule_action) for r in await self.rules])
        if rule_action == 'is_auto_approval':
            ret = any(ret)
        elif rule_action == 'approver':
            ret = [a for r in ret for a in r.split(',')]

        logger.debug('Ticket.get_rule_actions(%s): %s', rule_action, ret)
        return ret

    async def get_flow_policy(self):
        associates = await TicketPolicy.get_by_ticket_name(self.provider_object, without_default=True, desc=True)
        for associate in associates:
            if associate.match(self.params):
                return await Policy.get(id_=associate.policy_id)
        policy_id = await TicketPolicy.default_associate(self.provider_object)
        return await Policy.get(id_=policy_id)

    # 节点流转依据创建时 annotation 记录的节点信息, 若是节点变更前有未审批的工单则以原记录方式流转，否则需重提
    @property
    def init_node(self):
        nodes = self.annotation.get("nodes")
        if not nodes or len(nodes) == 0:
            return None
        return nodes[0]

    def next_node(self, node_name):
        nodes = self.annotation.get("nodes")
        for index, node in enumerate(nodes):
            if node.get("name") == node_name:
                return nodes[index+1] if (index != len(nodes)-1) else None

    def is_end_node(self, node_name):
        nodes = self.annotation.get("nodes")
        for index, node in enumerate(nodes):
            if node.get("name") == node_name:
                return index == len(nodes)-1
        return False

    def policy_auto_approved(self):
        return len(self.annotation.get("nodes")) == 1 and self.init_node.get("node_type")  == NodeType.CC.value

    def is_cc_node(self, node_name):
        for node in self.annotation.get("nodes"):
            if node.get("name") == node_name and node.get("node_type") == NodeType.CC.value:
                return True
        return False

    async def get_node_approvers(self, node_name):
        for node in self.annotation.get("nodes"):
            if node.get("name") != node_name:
                continue
            approver_type = node.get("approver_type") or ApproverType.PEOPLE
            approvers = node.get("approvers")
            if approvers and approver_type == ApproverType.PEOPLE:
                return approvers
            # 如果节点approvers为空 根据参数获取 app name 从而判断取哪个应用的负责人审批
            if approver_type == ApproverType.APP_OWNER:
                approvers = self.params.get("app")
            if approver_type == ApproverType.DEPARTMENT:
                approvers = self.params.get("department")
            provider = get_approver_provider(approver_type)
            return await provider.get_approver_members(approvers)
        return ""

    async def all_flow_approvers(self):
        all_approvers = []
        for node in self.annotation.get("nodes"):
            approver_type = node.get("approver_type") or ApproverType.PEOPLE
            node_approvers = node.get("approvers")
            # 如果节点approvers为空 根据参数获取 app name 从而判断取哪个应用的负责人审批
            if approver_type == ApproverType.APP_OWNER and node_approvers == "":
                node_approvers = self.params.get("app")
            if approver_type == ApproverType.DEPARTMENT and node_approvers == "":
                node_approvers = self.params.get("department")
            provider = get_approver_provider(approver_type)
            node_approvers = await provider.get_approver_members(node_approvers)
            for member in node_approvers.split(","):
                if member not in all_approvers:
                    all_approvers.append(member)
        return all_approvers

    def annotate(self, dict_=None, **kw):
        d = dict_ or {}
        d.update(kw)
        self.annotation = self.annotation or {}
        self.annotation.update(d)

    @property
    def is_confirmed(self):
        return self.confirmed_by or self.is_approved is not None

    @property
    def execution_result_url(self):
        if not self.annotation:
            return None
        return self.annotation.get('execution', {}).get('result_url')

    @property
    def is_auto_approved(self):
        if not self.annotation:
            return False
        return self.annotation.get('auto_approved', False)

    @property
    def web_url(self):
        return f'{DEFAULT_BASE_URL}/ticket/{self.id}'

    def check_confirmed(self):
        if self.is_confirmed:
            op = 'approved' if self.is_approved else 'rejected'
            msg = 'already %s by %s' % (op, self.confirmed_by)
            return True, msg
        return False, 'not confirmed yet'

    def set_approval_log(self, by_user=SYSTEM_USER, operated_type="approved"):
        approval_log = self.annotation.get("approval_log")
        approval_log.append(dict(node=self.annotation.get("current_node"), approver=by_user, operated_type=operated_type, operated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.annotate(approval_log=approval_log)

    async def node_transation(self):
        current_node = self.annotation.get("current_node")
        if self.is_end_node(current_node):
            return True
        else:
            next_node = self.next_node(current_node)
            self.annotate(current_node=next_node.get("name"))
            self.annotate(approvers=await self.get_node_approvers(next_node.get("name")))
            if next_node.get("node_type") == NodeType.CC.value:
                self.set_approval_log(operated_type="cc")
                await self.notify(TicketPhase.REQUEST)
                if self.is_end_node(next_node.get("name")):
                    return True
                next_again = self.next_node(next_node.get("name"))
                self.annotate(current_node=next_again.get("name"))
                self.annotate(approvers=await self.get_node_approvers(next_again.get("name")))
            return False

    async def pre_approve(self):
        if self.policy_auto_approved():
            self.annotate(auto_approved=True)
            self.set_approval_log(operated_type="cc")
            self.is_approved = True
            self.confirmed_by = SYSTEM_USER
            self.confirmed_at = datetime.now()

        if len(self.annotation.get("nodes")) != 1 and self.is_cc_node(self.init_node.get("name")):
            self.set_approval_log(operated_type="cc")
            await self.notify(TicketPhase.REQUEST)
            next_node = self.next_node( self.annotation.get("current_node"))
            self.annotate(current_node=next_node.get("name"))
            self.annotate(approvers=await self.get_node_approvers(next_node.get("name")))
        return True, "success"

    async def approve(self, by_user=None):
        is_confirmed, msg = self.check_confirmed()
        if is_confirmed:
            return False, msg

        self.set_approval_log(by_user=by_user or SYSTEM_USER)
        await self.notify(TicketPhase.APPROVAL)
        is_end_node = await self.node_transation()
        if is_end_node:
            self.is_approved = True
            self.confirmed_by = by_user or SYSTEM_USER
            self.confirmed_at = datetime.now()
            return True, 'Success'
        else:
            return True, 'Wait for next approval node.'

    async def reject(self, by_user):
        is_confirmed, msg = self.check_confirmed()
        if is_confirmed:
            return False, msg

        self.confirmed_by = by_user
        self.is_approved = False
        self.confirmed_at = datetime.now()

        self.set_approval_log(by_user=by_user or SYSTEM_USER, operated_type="rejected")
        await self.notify(TicketPhase.APPROVAL)
        return True, 'Success'

    def execute(self):
        provider = get_provider(self.provider_type)

        logger.info('run action %s, params: %s', self.provider_object, self.handle_extra_params())
        self.annotate(execution_submitted=True)
        execution, msg = provider.exec_ticket(self.provider_object, self.handle_extra_params())
        annotate = provider.get_exec_annotation(execution)
        if not execution:
            self.annotate(execution_creation_success=False, execution_creation_msg=msg)
            return execution, msg

        self.executed_at = datetime.now()
        self.annotate(execution=annotate, execution_creation_success=True, execution_creation_msg=msg)

        # we don't save the ticket here, we leave it outside
        return execution, 'Success. <a href="%s" target="_blank">result</a>' % (execution.result_url,)

    def get_result(self):
        provider = get_provider(self.provider_type)
        exec_annotation = self.annotation.get('execution', {})
        return provider.get_exec_result(exec_annotation)

    def get_result_log(self, output_id):
        provider = get_provider(self.provider_type)
        return provider.get_exec_log(output_id)

    async def notify(self, phase):
        logger.info('Ticket notify: %s: %s', phase, self)
        assert isinstance(phase, TicketPhase)

        for method in NOTIFICATION_METHODS:
            module, _class = method.split(':')
            try:
                notify = getattr(importlib.import_module(module), _class)
                await notify(phase, self).send()
            except Exception as e:
                report()
                logger.warning('notify to %s failed: %s', method, e)

    def generate_callback_url(self):
        """
        generate callback url for ticket mark status call back
        providers should call this url with http post and mark ticket's execution status
        :return: callback url
        """
        # todo: replace hardcode with url_path current url_path not working somehow
        callback_url = f'api/ticket/mark/{self.id}'
        jwt_token = jwt.encode({'alg': 'HS256'}, {'ticket_id': self.id, 'op': 'mark'}, SESSION_SECRET_KEY)
        callback_url_payload = {"token": jwt_token}
        return f"{DEFAULT_BASE_URL}/{callback_url}?{urlencode(callback_url_payload, quote_via=quote_plus)}"

    def handle_extra_params(self):
        """fill up callback params in config, replace with callback url"""
        if self.extra_params is None:
            return self.params
        for param in TICKET_CALLBACK_PARAMS:
            if param in self.extra_params:
                params_dict = {param: self.generate_callback_url()}
                params_dict.update(self.params)
                logger.debug(f"params for callback {params_dict}")
                return params_dict
        return self.params
