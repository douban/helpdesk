# coding: utf-8

import logging
from datetime import datetime
from typing import Optional

from authlib.jose import jwt, errors as jwterrors
from starlette.responses import RedirectResponse  # NOQA
from starlette.authentication import requires, has_required_scope  # NOQA
from fastapi import Query, HTTPException, Depends, Request

from helpdesk import config
from helpdesk.libs.db import extract_filter_from_query_params
from helpdesk.models.provider import get_provider
from helpdesk.models.db.ticket import Ticket, TicketPhase
from helpdesk.models.db.param_rule import ParamRule
from helpdesk.models.action_tree import action_tree
from helpdesk.models.user import User
from helpdesk.libs.dependency import get_current_user, require_admin

from . import router
from .schemas import MarkTickets, ParamRule as ParamRuleSchema, OperateTicket, QeuryKey

logger = logging.getLogger(__name__)


@router.get('/')
async def index():
    return dict(msg='Hello API')


@router.get('/user/me')
async def user(current_user: User = Depends(get_current_user)) -> dict:
    return current_user


@router.get('/admin_panel/{target_object}/{config_type}')
async def get_admin_panel_config(target_object: str, config_type: str,
                                 _: User = Depends(require_admin)):
    action_tree_leaf = action_tree.find(target_object) if target_object != '' else action_tree.first()
    if not action_tree_leaf:
        raise HTTPException(status_code=404, detail='Target object not found')
    action = action_tree_leaf.action

    if config_type not in ('param_rule',):
        raise HTTPException(status_code=400, detail='Config type not supported')

    param_rules = await ParamRule.get_all_by_provider_object(action.target_object)
    return param_rules


@router.post('/admin_panel/{target_object}/{config_type}/{op}')
async def admin_panel(target_object: str, config_type: str, param_rule: ParamRuleSchema,
                      _: User = Depends(require_admin), op: Optional[str] = None):
    if target_object != '':
        action_tree_leaf = action_tree.find(target_object)
    else:
        action_tree_leaf = action_tree.first()
    if not action_tree_leaf:
        raise HTTPException(status_code=404, detail='Target object not found')
    action = action_tree_leaf.action

    if config_type not in ('param_rule',):
        raise HTTPException(status_code=400, detail='Config type not supported')

    if config_type == 'param_rule':
        if op not in ('add', 'del'):
            raise HTTPException(status_code=400, detail='Operation not supported')

        if op == 'add':
            new_rule = ParamRule(
                id=param_rule.id,
                title=param_rule.title,
                provider_object=action.target_object,
                rule=param_rule.rule,
                is_auto_approval=param_rule.is_auto_approval,
                approver=param_rule.approver)
            id_ = await new_rule.save()
            param_rule_added = await ParamRule.get(id_)
            return param_rule_added
        if op == 'del':
            if not param_rule.id:
                raise HTTPException(status_code=400, detail='Param rule id is required')
            return await ParamRule.delete(param_rule.id) == param_rule.id


@router.get('/action_tree')
async def action_tree_list(_: User = Depends(get_current_user)):
    def node_formatter(node, children):
        if node.is_leaf:
            return node.action

        sub_node_info = {
            'name': node.name,
            'children': children,
        }
        return [sub_node_info] if node.parent is None else sub_node_info

    return action_tree.get_tree_list(node_formatter)


@router.get('/action/{target_object}')
@router.post('/action/{target_object}')
async def action(target_object: str, request: Request, current_user: User = Depends(get_current_user)):
    target_object = target_object.strip('/')

    # check if action exists
    action = action_tree.get_action_by_target_obj(target_object)
    if not action:
        raise HTTPException(status_code=404, detail='Target object not found')

    provider = get_provider(action.provider_type)

    if request.method == 'GET':
        return action.to_dict(provider, current_user)

    if request.method == 'POST':
        form = await request.form()
        ticket, msg = await action.run(provider, form, current_user)
        msg_level = 'success' if bool(ticket) else 'error'
        if not bool(ticket):
            raise HTTPException(status_code=500, detail=msg)
        return dict(ticket=ticket, msg=msg, msg_level=msg_level, debug=config.DEBUG)


@router.post('/ticket/mark/{ticket_id}')
async def mark_ticket(ticket_id: int, mark: MarkTickets, token: Optional[str] = None):
    """call helpdesk_ticket op to handle this handler only make authenticate disappear for provider"""
    # verify jwt for callback url
    try:
        payload = jwt.decode(token, config.SESSION_SECRET_KEY)
        logger.debug(f'received callback req: {payload}')
        assert payload['ticket_id'] == ticket_id
    except (jwterrors.BadSignatureError, AssertionError):
        raise HTTPException(status_code=403, detail='Invalid token')
    helpdesk_ticket = await Ticket.get(ticket_id)
    if not helpdesk_ticket:
        raise HTTPException(status_code=404, detail='Ticket not found')

    try:
        helpdesk_ticket.annotate(execution_status=mark.execution_status, final_exec_status=True)
        logger.debug(f"helpdesk_ticket annotation: {helpdesk_ticket.annotation}")
        # add notification to helpdesk_ticket mark action
        await helpdesk_ticket.notify(TicketPhase.MARK)
        await helpdesk_ticket.save()
    except (RuntimeError, AssertionError) as e:
        raise HTTPException(status_code=400, detail=f'decode mark body error: {str(e)}')
    return dict(msg='Success')


@router.post('/ticket/{ticket_id}/{op}')
async def ticket_op(ticket_id: int, op: str,
                    operate_data: OperateTicket, current_user: User = Depends(get_current_user)):
    if op not in ('approve', 'reject', 'close'):
        raise HTTPException(status_code=400, detail='Operation not supported')

    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail='Ticket not found')

    if op == 'close':
        "申请人才可主动关闭工单"
        if ticket.submitter != current_user.name:
            raise HTTPException(status_code=403, detail='Permission denied, only submitter can close')
        if ticket.status != "pending":
            raise HTTPException(status_code=400, detail='Ticket not pending, can not be closed')
        ticket.annotate(closed=True)
        ticket.confirmed_by = current_user.name
        ticket.confirmed_at = datetime.now()
        ticket.reason = operate_data.reason
        id_ = await ticket.save()
        if not id_:
            raise HTTPException(status_code=500, detail='ticket executed closed but failed to save state')
        await ticket.notify(TicketPhase.APPROVAL)
        return dict(msg='Success')

    if not await ticket.can_admin(current_user):
        raise HTTPException(status_code=403, detail='Permission denied')

    if op == 'approve':
        ret, msg = await ticket.approve(by_user=current_user.name)
        if not ret:
            raise HTTPException(status_code=400, detail=msg)
        if ret and "Success" not in msg:
            await ticket.notify(TicketPhase.REQUEST)
            ticket_id = await ticket.save()
            if not ticket_id:
                raise HTTPException(status_code=500, detail='Failed to save ticket info when has next approval')
            return dict(msg='Waiting for the approval of the next level')
        execution, msg = ticket.execute()
        if not execution:
            raise HTTPException(status_code=400, detail=msg)
    elif op == 'reject':
        if operate_data.reason:
            ticket.reason = operate_data.reason
        ret, msg = await ticket.reject(by_user=current_user.name)
        if not ret:
            raise HTTPException(status_code=400, detail=msg)

    id_ = await ticket.save()
    if not id_:
        msg = 'ticket executed but failed to save state' if op == 'approve' else 'Failed to save ticket state'
        raise HTTPException(status_code=500, detail=msg)
    return dict(msg='Success')


def extra_dict(d):
    id_ = d['id']
    return dict(
        url=f"/ticket/{id_}",
        approve_url=f"/api/ticket/{id_}/approve",
        reject_url=f"/api/ticket/{id_}/reject",
        api_url=f"/api/ticket/{id_}",
        **d)


@router.get('/ticket')
async def list_ticket(page: Optional[str] = None, pagesize: Optional[str] = None,
                      order_by: Optional[str] = None, desc: bool = False, current_user: User = Depends(get_current_user),
                      query_key: Optional[QeuryKey] = None, query_value: Optional[str] = None):
    query_params={'page': page, 'page_size': pagesize, 'order_by': order_by, 'desc': desc}
    if query_key and query_value:
        query_params[query_key] = query_value
    filter_ = extract_filter_from_query_params(query_params=query_params, model=Ticket)
    if page and page.isdigit():
        page = max(1, int(page))
    else:
        page = 1
    if pagesize and pagesize.isdigit():
        pagesize = max(1, int(pagesize))
        pagesize = min(pagesize, config.TICKETS_PER_PAGE)
    else:
        pagesize = config.TICKETS_PER_PAGE
    if desc and str(desc).lower() == 'false':
        desc = False
    else:
        desc = True
    kw = dict(filter_=filter_, order_by=order_by, desc=desc, limit=pagesize, offset=(page - 1) * pagesize)

    if current_user.is_admin:
        tickets = await Ticket.get_all(**kw)
        total = await Ticket.count(filter_=filter_)
    else:
        # only show self tickets if not admin
        tickets = await Ticket.get_all_by_submitter(submitter=current_user.name, **kw)
        total = await Ticket.count_by_submitter(submitter=current_user.name, filter_=filter_)

    return dict(
        tickets=[extra_dict(t.to_dict(show=True)) for t in tickets],
        page=page,
        page_size=pagesize,
        total=total,
    )


@router.get('/ticket/{ticket_id}')
@router.post('/ticket/{ticket_id}')
async def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user)):
    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    if not await ticket.can_view(current_user):
        raise HTTPException(status_code=403, detail='Permission denied')
    tickets = [ticket]
    total = 1
    return dict(
        tickets=[extra_dict(t.to_dict(show=True)) for t in tickets],
        total=total,
    )


@router.get('/ticket/{ticket_id}/result')
async def ticket_result(ticket_id: int, exec_output_id: Optional[str] = None, _: User = Depends(get_current_user)):
    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    execution, msg = ticket.get_result(execution_output_id=exec_output_id)
    if not execution:
        raise HTTPException(status_code=404, detail=msg)
    # update ticket status by result
    if not exec_output_id:
        annotation_execution_status = ticket.annotation.get('execution_status')
        final_exec_status = ticket.annotation.get('final_exec_status')
        try:
            exec_status = execution.get('status')
            if exec_status and annotation_execution_status != exec_status \
                    and not final_exec_status:
                ticket.annotate(execution_status=exec_status)
                await ticket.save()
        except AttributeError as e:
            logger.warning(f"can not get status from execution, error: {str(e)}")
    return execution
