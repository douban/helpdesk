# coding: utf-8

import logging

import sentry_sdk
from sentry_asgi import SentryMiddleware

from starlette.applications import Starlette
from starlette.routing import Mount, Route, Router  # NOQA
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from helpdesk.libs.auth import SessionAuthBackend
from helpdesk.config import DEBUG, SESSION_SECRET_KEY, SESSION_TTL, SENTRY_DSN
from helpdesk.views.api import bp as api_bp


def create_app():
    sentry_sdk.init(dsn=SENTRY_DSN)

    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)
    logging.getLogger('multipart').setLevel(logging.INFO)
    logging.getLogger('uvicorn').setLevel(logging.INFO)

    app = Starlette(
        debug=DEBUG, routes=[
            Mount('/api', app=api_bp, name='api'),
        ])

    app.add_middleware(AuthenticationMiddleware, backend=SessionAuthBackend())
    app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=SESSION_TTL)
    app.add_middleware(GZipMiddleware)
    app.add_middleware(SentryMiddleware)

    # NOTE: redirect in app level is evil, do it in your load balancer instead.
    # from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
    # from helpdesk.config import FORCE_HTTPS
    # if FORCE_HTTPS:
    #     app.add_middleware(HTTPSRedirectMiddleware)

    return app


app = create_app()
