# coding: utf-8

import base64
import logging
import binascii

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
        logger.debug('request.session: %s, user: %s', request.session, request.session.get('user'))
        if not request.session.get('user'):
            return
        return AuthCredentials(["authenticated"]), SimpleUser(request.session['user'])


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

    logger.debug('form: %s, user: %s, password: %s', form, user, password)

    provider = get_provider(PROVIDER)
    token, msg = provider.authenticate(user, password)

    request.session['user'] = user
    request.session['token'] = token

    logger.debug('get token: %s, msg: %s', token, msg)

    return token, msg


def unauth(request):
    request.session.pop('token', None)
    return request.session.pop('user', None)
