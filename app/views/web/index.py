# coding: utf-8

# from starlette.responses import PlainTextResponse

import logging

from app.libs.template import render
from app.models.action_tree import action_tree
from app.config import DEBUG

from . import bp

logger = logging.getLogger(__name__)


@bp.route('/{full_path:path}', methods=['GET', 'POST'])
async def index(request):
    full_path = request.path_params['full_path']
    target_object = full_path.strip('/')
    action = (action_tree.find(target_object) or action_tree.first()).action

    extra_context = {}
    if request.method == 'POST':
        form = await request.form()
        execution, msg = action.run(form)
        msg_level = 'success' if bool(execution) else 'danger'

        extra_context = dict(execution=execution,
                             msg=msg,
                             msg_level=msg_level)

    return render('action_form.html',
                  dict(request=request,
                       action_tree=action_tree,
                       action=action,
                       debug=DEBUG,
                       **extra_context))

# async def
# request.session
