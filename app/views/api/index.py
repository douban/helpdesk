# coding: utf-8

import logging

from sqlalchemy import true, and_

from starlette.responses import RedirectResponse  # NOQA
from starlette.authentication import requires, has_required_scope  # NOQA

from app import config
from app.libs.rest import jsonize, check_parameter, json_validator
from app.libs.template import url_for
from app.models.provider import get_provider_by_action_auth
from app.models.db.ticket import Ticket
from app.models.db.param_rule import ParamRule
from app.models.action_tree import action_tree
from app.views.api.errors import ApiError, ApiErrors

from . import bp

logger = logging.getLogger(__name__)


@bp.route('/favicon.ico', methods=['GET'])
async def favicon(request):
    return RedirectResponse(url=request.url_for('static', path='/images/favicon.ico'))


@bp.route('/')
@jsonize
async def index(request):
    return dict(msg='Hello API')


@bp.route('/user/me', methods=['GET'])
@requires(['authenticated'])
@jsonize
async def user(request):
    return request.user


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

            param_rule = ParamRule(id=payload.get('id'),
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
async def action(request):
    target_object = request.path_params.get('target_object', '').strip('/')

    # check if action exists
    action = action_tree.get_action_by_target_obj(target_object)
    if not action:
        raise ApiError(ApiErrors.not_found)

    # check provider permission
    provider = get_provider_by_action_auth(request, action)
    if not provider:
        raise ApiError(ApiErrors.forbidden)

    if request.method == 'GET':
        return action.to_dict(provider)

    if request.method == 'POST':
        form = await request.form()
        ticket = None
        ticket, msg = await action.run(provider, form,
                                       is_admin=has_required_scope(request, ['admin']))
        msg_level = 'success' if bool(ticket) else 'error'

        return dict(ticket=ticket,
                    msg=msg,
                    msg_level=msg_level,
                    debug=config.DEBUG,
                    provider=provider,
                    )


@bp.route('/ticket/{ticket_id:int}/{op}', methods=['POST'])
@jsonize
@requires(['authenticated'])
async def ticket_op(request):
    ticket_id = request.path_params['ticket_id']
    op = request.path_params['op']
    if op not in ('approve', 'reject'):
        raise ApiError(ApiErrors.unknown_operation)

    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise ApiError(ApiErrors.not_found)

    if not await ticket.can_admin(request.user):
        raise ApiError(ApiErrors.forbidden)

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
    await ticket.notify('approval')
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
        return dict(url=url_for('api:ticket', request, ticket_id=id_),
                    approve_url=url_for('api:ticket_op', request, ticket_id=id_, op='approve'),
                    reject_url=url_for('api:ticket_op', request, ticket_id=id_, op='reject'),
                    api_url=url_for('api:ticket', request, ticket_id=id_),
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
    ticket = None
    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise ApiError(ApiErrors.not_found)

    execution, msg = ticket.get_result()

    if not execution:
        raise ApiError(ApiErrors.unknown_exception, description=msg)
    return execution


def extract_filter_from_query_params(query_params=None, model=None, exclude_keys=None):
    if not hasattr(query_params, 'items'):
        raise ValueError('query_params has no items method')
    if not model:
        raise ValueError('Model must be set')
    if exclude_keys is None:
        exclude_keys = ['page', 'pagesize', 'order_by', 'desc']
        # initialize filter by iterating keys in query_params
    filter_ = true()
    for (key, value) in query_params.items():
        if key in exclude_keys:
            continue
        if key.endswith('__icontains'):
            key = key.split('__icontains')[0]
            filter_ = and_(filter_, model.__table__.c[key].icontains(value))
        elif key.endswith('__in'):
            key = key.split('__in')[0]
            value = value.split(',')
            filter_ = and_(filter_, model.__table__.c[key].in_(value))
        else:
            filter_ = and_(filter_, model.__table__.c[key] == value)
    return filter_, ''
