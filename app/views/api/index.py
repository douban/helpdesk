# coding: utf-8

from starlette.responses import PlainTextResponse

from . import bp


@bp.route('/')
async def index(request):
    return PlainTextResponse('Hello API')
