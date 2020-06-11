# coding: utf-8

import logging
import jwt

from starlette.responses import RedirectResponse  # NOQA
from starlette.authentication import requires, has_required_scope  # NOQA

from helpdesk import config
from helpdesk.libs.rest import jsonize, check_parameter, json_validator
from helpdesk.libs.db import extract_filter_from_query_params
from helpdesk.models.provider import get_provider
from helpdesk.models.db.ticket import Ticket, TicketPhase
from helpdesk.models.db.param_rule import ParamRule
from helpdesk.models.action_tree import action_tree
from helpdesk.views.api.errors import ApiError, ApiErrors

from . import bp

logger = logging.getLogger(__name__)


@bp.route('/')
@jsonize
async def index(request):
    return dict(msg='Hello API')


@bp.route('/user/me', methods=['GET'])
@requires(['authenticated'])
@jsonize
async def user(request):
    result = request.user.to_dict()
    result['is_admin'] = request.user.is_admin
    return result


@bp.route('/admin_panel/{target_object}/{config_type}', methods=['GET'])
@bp.route('/admin_panel/{target_object}/{config_type}/{op}', methods=['POST'])
@requires(['authenticated', 'admin'])
@jsonize
async def admin_panel(request):
    target_object = request.path_params.get('target_object', '')
    target_object = target_object.strip('/')

    action_tree_leaf = action_tree.find(target_object) if target_object != '' else action_tree.first()
    if not action_tree_leaf:
        raise ApiError(ApiErrors.not_found)
    action = action_tree_leaf.action

    config_type = request.path_params.get('config_type')
    if config_type not in ('param_rule',):
        raise ApiError(ApiErrors.unknown_config_type)

    if config_type == 'param_rule':
        return await config_param_rule(request, action)
    return action


async def config_param_rule(request, action):
    if request.method == 'POST':
        op = request.path_params['op']
        if op not in ('add', 'del'):
            raise ApiError(ApiErrors.unknown_operation)

        payload = await request.json()
        if op == 'add':
            rule = check_parameter(payload, 'rule', str, json_validator)

            param_rule = ParamRule(
                id=payload.get('id'),
                title=payload.get('title', 'Untitled'),
                provider_object=action.target_object,
                rule=rule,
                is_auto_approval=payload.get('is_auto_approval', False),
                approver=payload.get('approver'))
            id_ = await param_rule.save()
            param_rule_added = await ParamRule.get(id_)
            return param_rule_added
        elif op == 'del':
            id_ = check_parameter(payload, 'id', int)
            return await ParamRule.delete(id_) == id_

    param_rules = await ParamRule.get_all_by_provider_object(action.target_object)
    return param_rules


@bp.route('/action_tree')
@jsonize
@requires(['authenticated'])
async def action_tree_list(request):
    def node_formatter(node, children):
        if node.is_leaf:
            return node.action

        sub_node_info = {
            'name': node.name,
            'children': children,
        }
        return [sub_node_info] if node.parent is None else sub_node_info

    return action_tree.get_tree_list(node_formatter)


@bp.route('/action/{target_object}', methods=['GET', 'POST'])
@jsonize
@requires(['authenticated'])
async def action(request):
    target_object = request.path_params.get('target_object', '').strip('/')

    # check if action exists
    action = action_tree.get_action_by_target_obj(target_object)
    if not action:
        raise ApiError(ApiErrors.not_found)

    provider = get_provider(action.provider_type)

    if request.method == 'GET':
        return action.to_dict(provider)

    if request.method == 'POST':
        form = await request.form()
        is_admin = any(has_required_scope(request, (admin_role,)) for admin_role in config.ADMIN_ROLES)
        ticket, msg = await action.run(provider, form, is_admin=is_admin)
        msg_level = 'success' if bool(ticket) else 'error'

        return dict(ticket=ticket, msg=msg, msg_level=msg_level, debug=config.DEBUG)


@bp.route('/ticket/{ticket_id:int}/{op}', methods=['POST'])
@jsonize
@requires(['authenticated'])
async def ticket_op(request):
    ticket_id = request.path_params['ticket_id']
    op = request.path_params['op']
    if op not in ('approve', 'reject'):
        raise ApiError(ApiErrors.unknown_operation, description=f"unknown operation of {op}")

    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise ApiError(ApiErrors.not_found, description=f"ticket {ticket_id} not found!")

    if not await ticket.can_admin(request.user):
        raise ApiError(ApiErrors.forbidden, description=f"You are not allowed {op} action")

    if op == 'approve':
        ret, msg = ticket.approve(by_user=request.user.name)
        if not ret:
            raise ApiError(ApiErrors.unrepeatable_operation, description=msg)
        execution, msg = ticket.execute()
        if not execution:
            raise ApiError(ApiErrors.unknown_exception, description=msg)
    elif op == 'reject':
        ret, msg = ticket.reject(by_user=request.user.name)
        if not ret:
            raise ApiError(ApiErrors.unrepeatable_operation, description=msg)

    id_ = await ticket.save()
    if not id_:
        msg = 'ticket executed but failed to save state' if op == 'approve' else 'Failed to save ticket state'
        raise ApiError(ApiErrors.unknown_exception, description=msg)
    await ticket.notify(TicketPhase.APPROVAL)
    return dict(msg='Success')


@bp.route('/ticket/mark/{ticket_id:int}', methods=['POST'])
@jsonize
async def mark_ticket(request):
    """call ticket op to handle this handler only make authenticate disappear for provider"""
    # verify jwt for callback url
    token = request.query_params.get('token')
    ticket_id = request.path_params['ticket_id']

    try:
        payload = jwt.decode(token, config.SESSION_SECRET_KEY)
        logger.debug(f'recieved callback req: {payload}')
        assert payload['ticket_id'] == ticket_id
    except (jwt.exceptions.InvalidSignatureError, AssertionError):
        raise ApiError(ApiErrors.parameter_validation_failed, description="token error")
    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise ApiError(ApiErrors.not_found, description=f"ticket {ticket_id} not found!")

    try:
        data = await request.json()
        assert 'execution_status' in data, "mark body fields error"
        ticket.annotate(execution_status=data["execution_status"])
        logger.debug(f"tocket annotaion: {ticket.annotation}")
        # add notification to ticket mark action
        await ticket.notify(TicketPhase.MARK)
        await ticket.save()
    except (RuntimeError, AssertionError) as e:
        raise ApiError(ApiErrors.parameter_validation_failed, description=f'decode mark body error: {str(e)}')
    return dict(msg='Success')


@bp.route('/ticket', methods=['GET'])
@bp.route('/ticket/{ticket_id:int}', methods=['GET', 'POST'])
@jsonize
@requires(['authenticated'])
async def ticket(request):
    ticket_id = request.path_params.get('ticket_id')
    ticket = None
    if ticket_id:
        ticket = await Ticket.get(ticket_id)
        if not ticket:
            raise ApiError(ApiErrors.not_found)

    if request.method == 'POST':
        pass

    page = request.query_params.get('page')
    page_size = request.query_params.get('pagesize')
    order_by = request.query_params.get('order_by')
    desc = request.query_params.get('desc')
    filter_ = extract_filter_from_query_params(query_params=request.query_params, model=Ticket)
    if page and page.isdigit():
        page = max(1, int(page))
    else:
        page = 1
    if page_size and page_size.isdigit():
        page_size = max(1, int(page_size))
        page_size = min(page_size, config.TICKETS_PER_PAGE)
    else:
        page_size = config.TICKETS_PER_PAGE
    if desc and str(desc).lower() == 'false':
        desc = False
    else:
        desc = True
    kw = dict(filter_=filter_, order_by=order_by, desc=desc, limit=page_size, offset=(page - 1) * page_size)

    if ticket:
        if not await ticket.can_view(request.user):
            raise ApiError(ApiErrors.forbidden)
        tickets = [ticket]
        total = 1
    elif request.user.is_admin:
        tickets = await Ticket.get_all(**kw)
        total = await Ticket.count(filter_=filter_)
    else:
        # only show self tickets if not admin
        tickets = await Ticket.get_all_by_submitter(submitter=request.user.name, **kw)
        total = await Ticket.count_by_submitter(submitter=request.user.name, filter_=filter_)

    def extra_dict(d):
        id_ = d['id']
        return dict(
            url=f"/ticket/{id_}",
            approve_url=f"/ticket/{id_}/approve",
            reject_url=f"/ticket/{id_}/reject",
            api_url=f"/api/ticket/{id_}",
            **d)

    return dict(
        request=request,
        tickets=[extra_dict(t.to_dict(show=True)) for t in tickets],
        page=page,
        page_size=page_size,
        total=total,
    )


@bp.route('/ticket/{ticket_id:int}/result', methods=['GET'])
@jsonize
@requires(['authenticated'])
async def ticket_result(request):
    ticket_id = request.path_params.get('ticket_id')
    if not ticket_id:
        raise ApiError(ApiErrors.unknown_operation, description='Ticket id must be provided')

    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise ApiError(ApiErrors.not_found)

    output_execution_id = request.query_params.get('exec_output_id')
    execution, msg = ticket.get_result(execution_output_id=output_execution_id)
    if not execution:
        raise ApiError(ApiErrors.unknown_exception, description=msg)
    # update ticket status by result
    if not output_execution_id:
        annotation_execution_status = ticket.annotation.get('execution_status')
        try:
            exec_status = execution.get('status')
            if exec_status and annotation_execution_status != exec_status:
                ticket.annotate(execution_status=exec_status)
                await ticket.save()
        except AttributeError as e:
            logger.warning(f"can not get status from execution, error: {str(e)}")
    return execution
