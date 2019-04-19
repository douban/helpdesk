# coding: utf-8

# from starlette.responses import PlainTextResponse

from app.libs.template import render

from app.models.action_tree import action_tree

from . import bp


@bp.route('/')
def index(request):
    # return render('index.html', locals())
    return render('create_mfs_userhome.html', dict(request=request, action_tree=action_tree))
