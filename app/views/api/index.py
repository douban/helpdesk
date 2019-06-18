# coding: utf-8

import logging

from starlette.responses import RedirectResponse  # NOQA
from starlette.authentication import requires, has_required_scope  # NOQA

from app.libs.rest import jsonize, check_parameter, yaml_validator
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


@bp.route('/ticket/{ticket_id:int}', methods=['GET'])
@requires(['authenticated'])
@jsonize
async def ticket(request):
    ticket_id = request.path_params['ticket_id']
    ticket = await Ticket.get(ticket_id)
    if not ticket:
        raise ApiError(ApiErrors.not_found)
    if not await ticket.can_view(request.user):
        raise ApiError(ApiErrors.forbidden)
    return ticket


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
            rule = check_parameter(payload, 'rule', str, yaml_validator)

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
            ParamRule.delete(id_)
            return True

    param_rules = await ParamRule.get_all_by_provider_object(action.target_object)
    return param_rules
