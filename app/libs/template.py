# coding: utf-8

from starlette.templating import Jinja2Templates


templates = Jinja2Templates(directory='app/templates')


def render(template, context, status_code=200):
    # context must include the "request"
    return templates.TemplateResponse(template, context, status_code=status_code)
