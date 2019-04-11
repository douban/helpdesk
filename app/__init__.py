# coding: utf-8

from starlette.applications import Starlette
from starlette.routing import Mount, Route, Router
from starlette.staticfiles import StaticFiles

from app.views.web import bp as web_bp
from app.views.api import bp as api_bp


# web_bp.mount('/', StaticFiles(directory="app/static"))


def create_app():
    app = Starlette()

    print(api_bp)

    app = Router([
        Mount('/api', app=api_bp),
        Mount('/', app=web_bp),
    ])
    return app


app = create_app()
