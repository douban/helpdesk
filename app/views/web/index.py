# coding: utf-8

import logging
import urllib.parse

from starlette.responses import PlainTextResponse, RedirectResponse  # NOQA
from starlette.exceptions import HTTPException
from starlette.authentication import requires, has_required_scope  # NOQA

from app.libs.auth import authenticate, unauth
from app.libs.template import render
from app.models.provider import get_provider
from app.models.action_tree import action_tree
from app.models.db.ticket import Ticket
from app.config import DEBUG, PROVIDER, NO_AUTH_TARGET_OBJECTS, URL_RESET_PASSWORD, avatar_url_func

from . import bp

logger = logging.getLogger(__name__)


@bp.route('/favicon.ico', methods=['GET'])
async def favicon(request):
    return RedirectResponse(url=request.url_for('static', path='/images/favicon.ico'))


@bp.route('/login', methods=['GET', 'POST'])
async def login(request):
    extra_context = {}
    if request.method == 'POST':
        token, msg = await authenticate(request)

        if token:
            return_url = request.query_params.get('r', request.url_for('web:index', full_path=''))
            return RedirectResponse(url=return_url)

        extra_context = dict(msg=msg,
                             msg_level='danger')

    return render('login.html',
                  dict(request=request,
                       reset_pass_url=URL_RESET_PASSWORD,
                       debug=DEBUG,
                       **extra_context))


@bp.route('/logout', methods=['GET', 'POST'])
async def logout(request):
    unauth(request)
    return RedirectResponse(url=request.url_for('web:index', full_path=''))


# TODO: auth approver
@bp.route('/ticket/{ticket_id:int}/{op}', methods=['GET'])
async def ticket_op(request):
    ticket_id = request.path_params['ticket_id']
    op = request.path_params['op']
    if op not in ('approve', 'reject'):
        return PlainTextResponse('unknown operation', status_code=404)

    ticket = await Ticket.get(ticket_id)
    if not ticket:
        return PlainTextResponse('not found', status_code=404)

    if op == 'approve':
        ret, msg = ticket.approve(by_user=request.user.display_name)
        if not ret:
            return PlainTextResponse(msg)
        execution, msg = ticket.execute()
        if not execution:
            return PlainTextResponse(msg, status_code=500)
    elif op == 'reject':
        ret, msg = ticket.reject(by_user=request.user.display_name)
        if not ret:
            return PlainTextResponse(msg)

    id_ = await ticket.save()
    if not id_:
        msg = 'ticket executed but failed to save state' if op == 'approve' else 'Failed to save ticket state'
        return PlainTextResponse(msg, status_code=500)
    return PlainTextResponse('Success')


@bp.route('/{full_path:path}', methods=['GET', 'POST'])
async def index(request):
    full_path = request.path_params['full_path']
    target_object = full_path.strip('/')

    action_tree_leaf = action_tree.find(target_object) if target_object != '' else action_tree.first()
    if not action_tree_leaf:
        raise HTTPException(status_code=404)
    action = action_tree_leaf.action

    # auth
    _action_tree = action_tree
    if not has_required_scope(request, ['authenticated']):
        if action.target_object in NO_AUTH_TARGET_OBJECTS:
            _action_tree = action_tree_leaf
        else:
            return RedirectResponse(url=request.url_for('web:login') + '?r=' + urllib.parse.quote(request.url.path))

    provider = get_provider(PROVIDER, token=request.session.get('token'), user=request.user.display_name)

    extra_context = {}
    if request.method == 'POST':
        form = await request.form()
        execution_or_ticket, msg = await action.run(provider, form)
        msg_level = 'success' if bool(execution_or_ticket) else 'danger'
        execution = ticket = None
        if execution_or_ticket and execution_or_ticket.get('_class') == 'Ticket':
            ticket = execution_or_ticket
        else:
            execution = execution_or_ticket

        extra_context = dict(execution=execution,
                             ticket=ticket,
                             msg=msg,
                             msg_level=msg_level)

    return render('action_form.html',
                  dict(request=request,
                       avatar_url=avatar_url_func(request.user.display_name),
                       action_tree=_action_tree,
                       action=action,
                       provider=provider,
                       debug=DEBUG,
                       **extra_context))
