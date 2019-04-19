# coding: utf-8

from starlette.applications import Starlette
from starlette.routing import Mount, Route, Router
from starlette.staticfiles import StaticFiles

from app.views.web import bp as web_bp
from app.views.api import bp as api_bp


def create_app():
    static = StaticFiles(directory="app/static")

    app = Router([
        Mount('/api', app=api_bp, name='api'),
        Mount('/static', app=static, name='static'),
        Mount('/', app=web_bp, name='web'),
    ])
    return app


app = create_app()
