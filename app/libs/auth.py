# coding: utf-8

import base64
import logging
import binascii
from datetime import datetime, timedelta

from starlette.authentication import (AuthenticationBackend,
                                      AuthenticationError, SimpleUser,
                                      AuthCredentials)

logger = logging.getLogger(__name__)


class BasicAuthBackend(AuthenticationBackend):
    '''
    copy from https://www.starlette.io/authentication/
    '''
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise AuthenticationError('Invalid basic auth credentials')

        username, _, password = decoded.partition(":")
        # You'd want to verify the username and password here,
        # possibly by installing `DatabaseMiddleware`
        # and retrieving user information from `request.database`.

        # scopes
        return AuthCredentials(["authenticated"]), SimpleUser(username)


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        from app.models.user import User
        from app.models.provider import get_provider
        from app.config import PROVIDER

        logger.debug('request.session: %s, user: %s', request.session, request.session.get('user'))
        if not all([request.session.get('user'), request.session.get('token'), request.session.get('expiry')]):
            return
        # check token expiry, e.g. '2019-05-28T10:34:03.240708Z'
        expiry = request.session['expiry']
        if datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S.%fZ") < datetime.utcnow() + timedelta(minutes=1):
            logger.debug('token expiry time is in 1 minute, unauth.')
            unauth(request)
            return

        username = request.session['user']
        token = request.session['token']

        provider = get_provider(PROVIDER, token=token, user=username)
        user = User(username=username, provider=provider)
        return user.auth_credentials, user


async def authenticate(request):
    '''Get user, password from request.form and authenticate with the provider to get a token,
    then set the token to session.
    '''
    from app.config import PROVIDER
    from app.models.provider import get_provider

    if request.method != 'POST':
        return

    form = await request.form()
    user = form.get('user')
    password = form.get('password')

    system_provider = get_provider(PROVIDER)
    token, msg = system_provider.authenticate(user, password)

    logger.debug('get token: %s, msg: %s', token, msg)

    if token:
        request.session['user'] = user
        request.session['token'] = token['token']
        request.session['expiry'] = token['expiry']

    return token, msg


def unauth(request):
    request.session.pop('token', None)
    request.session.pop('expiry', None)
    return request.session.pop('user', None)
