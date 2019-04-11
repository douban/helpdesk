# coding: utf-8

from starlette.responses import PlainTextResponse

from . import bp


@bp.route('/')
def index(request):
    return PlainTextResponse('Hello web')
