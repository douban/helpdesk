# coding: utf-8

import logging

from starlette.responses import RedirectResponse  # NOQA
from starlette.authentication import requires, has_required_scope  # NOQA

from app import config
from app.libs.rest import jsonize, check_parameter, json_validator
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
        execution_or_ticket, msg = await action.run(provider, form,
                                                    is_admin=has_required_scope(request, ['admin']))
        msg_level = 'success' if bool(execution_or_ticket) else 'error'
        execution = ticket = None
        if execution_or_ticket and execution_or_ticket.get('_class') == 'Ticket':
            ticket = execution_or_ticket
        else:
            execution = execution_or_ticket

        return dict(execution=execution,
                    ticket=ticket,
                    msg=msg,
                    msg_level=msg_level,
                    debug=config.DEBUG,
                    provider=provider,
                    )


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

    extra_context = {}
    if request.method == 'POST':
        pass

    page = request.query_params.get('page')
    page_size = request.query_params.get('pagesize')
    if page and page.isdigit():
        page = max(1, int(page))
    else:
        page = 1
    if page_size and page_size.isdigit():
        page_size = max(1, int(page_size))
        page_size = min(page_size, config.TICKETS_PER_PAGE)
    else:
        page_size = config.TICKETS_PER_PAGE
    kw = dict(desc=True, limit=page_size, offset=(page - 1) * page_size)

    if ticket:
        if not await ticket.can_view(request.user):
            raise ApiError(ApiErrors.forbidden)
        tickets = [ticket]
        total = 1
    elif request.user.is_admin:
        tickets = await Ticket.get_all(**kw)
        total = await Ticket.count()
    else:
        # only show self tickets if not admin
        tickets = await Ticket.get_all_by_submitter(submitter=request.user.name, **kw)
        total = await Ticket.count_by_submitter(submitter=request.user.name)

    return dict(
        request=request,
        tickets=tickets,
        page=page,
        page_size=page_size,
        total=total,
        **extra_context
    )
