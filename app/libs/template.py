# coding: utf-8

import typing
import logging

import jinja2
from starlette.templating import Jinja2Templates as _Jinja2Templates, _TemplateResponse
from starlette.background import BackgroundTask

from app.config import DEFAULT_BASE_URL

logger = logging.getLogger(__name__)

_router = None


def set_router(router):
    global _router
    _router = router


class Jinja2Templates(_Jinja2Templates):
    def get_env(self, directory: str) -> "jinja2.Environment":
        @jinja2.contextfunction
        def url_for(context: dict, name: str, **path_params: typing.Any) -> str:
            """use request to generate url if request is presented in context, otherwise use configured url bash.
            """
            if 'request' in context:
                request = context["request"]
                return request.url_for(name, **path_params)
            else:
                url_path = _router.url_path_for(name, **path_params)
                return '%s%s' % (DEFAULT_BASE_URL, url_path)

        loader = jinja2.FileSystemLoader(directory)
        env = jinja2.Environment(loader=loader, autoescape=True)
        env.globals["url_for"] = url_for
        return env

    def get_template(self, name: str) -> "jinja2.Template":
        return self.env.get_template(name)

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ) -> _TemplateResponse:
        # if "request" not in context:
        #     raise ValueError('context must include a "request" key')
        template = self.get_template(name)
        return _TemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


templates = Jinja2Templates(directory='app/templates')
notification_templates = Jinja2Templates(directory='app/templates/notification')


def render(template, context, status_code=200):
    # context must include the "request"
    return templates.TemplateResponse(template, context, status_code=status_code)


def render_notification(template, context):
    import xml.etree.ElementTree as ET

    jinja_template = notification_templates.get_template(template)
    message = jinja_template.render(context)
    logger.debug('render_notification: message: %s', message)
    tree = ET.fromstring(message)
    title = ''.join(piece.text for piece in tree.findall('title'))
    content = ''.join(piece.text for piece in tree.findall('content'))
    return title, content
