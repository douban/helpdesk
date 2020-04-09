# coding: utf-8

import json
import logging
import urllib.parse

from starlette.responses import PlainTextResponse, RedirectResponse  # NOQA
from starlette.exceptions import HTTPException
from starlette.authentication import requires, has_required_scope  # NOQA

from app.libs.auth import authenticate, unauth
from app.libs.template import render, url_for
from app.models.provider import get_provider
from app.models.action_tree import action_tree
from app.models.db.ticket import Ticket
import app.config as config
from app.config import (DEBUG,
                        PROVIDER, NO_AUTH_TARGET_OBJECTS, URL_RESET_PASSWORD,
                        TICKETS_PER_PAGE)

from . import bp

logger = logging.getLogger(__name__)


@bp.exception_handler(404)
async def not_found(request, exc):
    return render('404.html', dict(request=request), status_code=exc.status_code)


@bp.exception_handler(500)
async def server_error(request, exc):
    return render('500.html', dict(request=request), status_code=exc.status_code)


@bp.route('/favicon.ico', methods=['GET'])
async def favicon(request):
    return RedirectResponse(url=url_for('static', request, path='/images/favicon.ico'))


@bp.route('/login', methods=['GET', 'POST'])
async def login(request):
    extra_context = {}
    if request.method == 'POST':
        token, msg = await authenticate(request)

        if token:
            return_url = request.query_params.get('r', url_for('web:index', request))
            return RedirectResponse(url=return_url)

        extra_context = dict(msg=msg,
                             msg_level='error')

    return render('login.html',
                  dict(request=request,
                       reset_pass_url=URL_RESET_PASSWORD,
                       debug=DEBUG,
                       config=config,
                       **extra_context))


@bp.route('/logout', methods=['GET', 'POST'])
async def logout(request):
    unauth(request)
    return RedirectResponse(url=url_for('web:index', request))


@bp.route('/ticket/{ticket_id:int}/{op}', methods=['GET'])
@requires(['authenticated'])
async def ticket_op(request):
    ticket_id = request.path_params['ticket_id']
    op = request.path_params['op']
    if op not in ('approve', 'reject'):
        return PlainTextResponse('unknown operation', status_code=404)

    ticket = await Ticket.get(ticket_id)
    if not ticket:
        return PlainTextResponse('not found', status_code=404)

    if not await ticket.can_admin(request.user):
        return PlainTextResponse('Permission Denied', status_code=403)

    if op == 'approve':
        ret, msg = ticket.approve(by_user=request.user.name)
        if not ret:
            return PlainTextResponse(msg)
        execution, msg = ticket.execute()
        if not execution:
            return PlainTextResponse(msg, status_code=500)
    elif op == 'reject':
        ret, msg = ticket.reject(by_user=request.user.name)
        if not ret:
            return PlainTextResponse(msg)

    id_ = await ticket.save()
    if not id_:
        msg = 'ticket executed but failed to save state' if op == 'approve' else 'Failed to save ticket state'
        return PlainTextResponse(msg, status_code=500)
    await ticket.notify('approval')
    return PlainTextResponse('Success')


@bp.route('/ticket', methods=['GET'])
@bp.route('/ticket/{ticket_id:int}', methods=['GET', 'POST'])
@requires(['authenticated'])
async def ticket(request):
    ticket_id = request.path_params.get('ticket_id')
    ticket = None
    if ticket_id:
        ticket = await Ticket.get(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404)

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
        page_size = min(page_size, TICKETS_PER_PAGE)
    else:
        page_size = TICKETS_PER_PAGE
    kw = dict(desc=True, limit=page_size, offset=(page - 1) * page_size)

    if ticket:
        if not await ticket.can_view(request.user):
            raise HTTPException(status_code=403)
        tickets = [ticket]
        total = 1
    elif request.user.is_admin(config.PROVIDER):
        tickets = await Ticket.get_all(**kw)
        total = await Ticket.count()
    else:
        # only show self tickets if not admin
        tickets = await Ticket.get_all_by_submitter(submitter=request.user.name, **kw)
        total = await Ticket.count_by_submitter(submitter=request.user.name)

    def extra_dict(d):
        id_ = d['id']
        return dict(url=url_for('web:ticket', request, ticket_id=id_),
                    approve_url=url_for('web:ticket_op', request, ticket_id=id_, op='approve'),
                    reject_url=url_for('web:ticket_op', request, ticket_id=id_, op='reject'),
                    api_url=url_for('api:ticket', request, ticket_id=id_),
                    **d)

    tickets_data = [extra_dict(t.to_dict(show=True)) for t in tickets]

    return render('ticket.html',
                  dict(request=request,
                       tickets=tickets,
                       tickets_data=json.dumps(tickets_data),
                       page=page,
                       page_size=page_size,
                       total=total,
                       debug=DEBUG,
                       config=config,
                       **extra_context))


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/{full_path:path}', methods=['GET', 'POST'])
async def index(request):
    full_path = request.path_params.get('full_path', '')
    target_object = full_path.strip('/')

    action_tree_leaf = action_tree.find(target_object) if target_object != '' else action_tree.first()
    if not action_tree_leaf:
        raise HTTPException(status_code=404)
    action = action_tree_leaf.action
    system_provider = get_provider(action.provider_type)

    # auth
    _action_tree = action_tree
    if not has_required_scope(request, ['authenticated']):
        if action.target_object in NO_AUTH_TARGET_OBJECTS:
            _action_tree = action_tree_leaf
            provider = system_provider
        else:
            return RedirectResponse(url=url_for('web:login', request) + '?r=' + urllib.parse.quote(request.url.path))
    else:
        provider = request.user.providers[action.provider_type]

    extra_context = {}
    if request.method == 'POST':
        form = await request.form()
        is_admin = any(has_required_scope(request, (admin_role,)) for admin_role in config.ADMIN_ROLES)
        execution_or_ticket, msg = await action.run(provider, form, is_admin=is_admin)
        msg_level = 'success' if bool(execution_or_ticket) else 'error'
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
                       action_tree=_action_tree,
                       action=action,
                       provider=provider,
                       menu_data=json.dumps(dict(openKeys=_action_tree.path_to(action_tree_leaf)[1:-1],
                                                 selectedKeys=[action.name])),
                       debug=DEBUG,
                       config=config,
                       **extra_context))
