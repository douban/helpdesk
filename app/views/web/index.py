# coding: utf-8

import logging
import urllib.parse

from starlette.responses import PlainTextResponse, RedirectResponse  # NOQA
from starlette.authentication import requires, has_required_scope  # NOQA

from app.libs.auth import authenticate, unauth
from app.libs.template import render
from app.models.provider import get_provider
from app.models.action_tree import action_tree
from app.config import DEBUG, PROVIDER, NO_AUTH_TARGET_OBJECTS, URL_RESET_PASSWORD, avatar_url_func

from . import bp

logger = logging.getLogger(__name__)


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


@bp.route('/{full_path:path}', methods=['GET', 'POST'])
async def index(request):
    full_path = request.path_params['full_path']
    target_object = full_path.strip('/')

    action_tree_leaf = action_tree.find(target_object) or action_tree.first()
    action = action_tree_leaf.action

    # auth
    _action_tree = action_tree
    if not has_required_scope(request, ['authenticated']):
        if action.target_object in NO_AUTH_TARGET_OBJECTS:
            _action_tree = action_tree_leaf
        else:
            return RedirectResponse(url=request.url_for('web:login') + '?r=' + urllib.parse.quote(request.url.path))

    provider = get_provider(PROVIDER, token=request.session.get('token'), user=request.session.get('user'))

    extra_context = {}
    if request.method == 'POST':
        form = await request.form()
        execution_or_ticket, msg = await action.run(provider, form)
        msg_level = 'success' if bool(execution_or_ticket) else 'danger'
        execution = ticket = None
        if execution_or_ticket.get('_class') == 'Ticket':
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
