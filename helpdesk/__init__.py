# coding: utf-8

import logging

import sentry_sdk
from sentry_asgi import SentryMiddleware

from starlette.applications import Starlette
from starlette.routing import Mount, Route, Router  # NOQA
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from helpdesk.libs.auth import SessionAuthBackend
from helpdesk.libs.proxy import ProxyHeadersMiddleware
from helpdesk.config import DEBUG, SESSION_SECRET_KEY, SESSION_TTL, SENTRY_DSN, TRUSTED_HOSTS
from helpdesk.views.api import bp as api_bp
from helpdesk.views.auth import bp as auth_bp


def create_app():
    sentry_sdk.init(dsn=SENTRY_DSN)

    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)
    logging.getLogger('multipart').setLevel(logging.INFO)
    logging.getLogger('uvicorn').setLevel(logging.INFO)

    routes = routes = [
        Mount('/api', app=api_bp, name='api'),
        Mount('/auth', app=auth_bp, name='auth'),
    ]
    middleware = [
        Middleware(ProxyHeadersMiddleware, trusted_hosts=TRUSTED_HOSTS),
        Middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=SESSION_TTL),
        Middleware(AuthenticationMiddleware, backend=SessionAuthBackend()),
        Middleware(GZipMiddleware),
        Middleware(SentryMiddleware),
    ]

    app = Starlette(debug=DEBUG, routes=routes, middleware=middleware)

    return app


app = create_app()
