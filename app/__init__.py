# coding: utf-8

import logging

from starlette.applications import Starlette  # NOQA
from starlette.routing import Mount, Route, Router  # NOQA
from starlette.staticfiles import StaticFiles

from app.config import DEBUG
from app.views.web import bp as web_bp
from app.views.api import bp as api_bp


def create_app():
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)
    logging.getLogger('multipart').setLevel(logging.INFO)
    logging.getLogger('uvicorn').setLevel(logging.INFO)

    static = StaticFiles(directory="app/static")

    app = Router([
        Mount('/api', app=api_bp, name='api'),
        Mount('/static', app=static, name='static'),
        Mount('/', app=web_bp, name='web'),
    ])
    return app


app = create_app()
