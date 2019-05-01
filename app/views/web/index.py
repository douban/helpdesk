# coding: utf-8

# from starlette.responses import PlainTextResponse

from app.libs.template import render
from app.models.action_tree import action_tree
from app.config import DEBUG

from . import bp


@bp.route('/{full_path:path}')
def index(request):
    full_path = request.path_params['full_path']
    target_object = full_path.strip('/')
    action = (action_tree.find(target_object) or action_tree.first()).action
    return render('action_form.html',
                  dict(request=request,
                       action_tree=action_tree,
                       action=action,
                       debug=DEBUG))
