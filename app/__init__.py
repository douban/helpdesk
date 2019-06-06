# coding: utf-8

import logging

import sentry_sdk
from sentry_asgi import SentryMiddleware

from starlette.applications import Starlette
from starlette.routing import Mount, Route, Router  # NOQA
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

import app.libs.template as template
from app.libs.auth import SessionAuthBackend
from app.config import DEBUG, SESSION_SECRET_KEY, SESSION_TTL, SENTRY_DSN, FORCE_HTTPS
from app.views.web import bp as web_bp
from app.views.api import bp as api_bp


def create_app():
    sentry_sdk.init(dsn=SENTRY_DSN)

    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)
    logging.getLogger('multipart').setLevel(logging.INFO)
    logging.getLogger('uvicorn').setLevel(logging.INFO)

    static = StaticFiles(directory="app/static")

    app = Starlette(debug=DEBUG, routes=[
        Mount('/api', app=api_bp, name='api'),
        Mount('/static', app=static, name='static'),
        Mount('/', app=web_bp, name='web'),
    ])

    # maybe skip some middleware for static?

    app.add_middleware(AuthenticationMiddleware, backend=SessionAuthBackend())
    app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=SESSION_TTL)
    app.add_middleware(GZipMiddleware)
    app.add_middleware(SentryMiddleware)
    if FORCE_HTTPS:
        app.add_middleware(HTTPSRedirectMiddleware)

    return app


app = create_app()
template.set_router(app.router)
