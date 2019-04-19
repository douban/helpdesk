# coding: utf-8

from starlette.templating import Jinja2Templates


templates = Jinja2Templates(directory='app/templates')


def render(template, context):
    return templates.TemplateResponse(template, context)
