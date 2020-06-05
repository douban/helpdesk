# coding: utf-8

import logging

import jinja2
from starlette.templating import Jinja2Templates as _Jinja2Templates, _TemplateResponse
from starlette.background import BackgroundTask

from helpdesk.config import DEFAULT_BASE_URL

logger = logging.getLogger(__name__)


class Jinja2Templates(_Jinja2Templates):
    def get_env(self, directory: str) -> "jinja2.Environment":
        loader = jinja2.FileSystemLoader(directory)
        env = jinja2.Environment(loader=loader, autoescape=True)
        env.globals["BASE_URL"] = DEFAULT_BASE_URL
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


notification_templates = Jinja2Templates(directory='templates/notification')


def render_notification(template, context):
    import xml.etree.ElementTree as ET

    jinja_template = notification_templates.get_template(template)
    message = jinja_template.render(context)
    logger.debug('render_notification: message: %s', message)
    tree = ET.fromstring(message)
    title = ''.join(piece.text for piece in tree.findall('title'))
    content = ''.join(piece.text for piece in tree.findall('content'))
    return title, content
