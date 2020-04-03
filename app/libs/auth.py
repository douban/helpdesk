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
        from app.config import ENABLED_PROVIDERS, AUTH_UNSUPPORT_PROVIDERS
        logger.debug('request.session: %s, user: %s', request.session, request.session.get('user'))

        for provider_type in ENABLED_PROVIDERS:
            if provider_type in AUTH_UNSUPPORT_PROVIDERS:
                continue
            if not all([request.session.get('user'), request.session.get(f'{provider_type}_token'),
                        request.session.get(f'{provider_type}_expiry')]):
                logger.error(f'{provider_type} auth error, unauth')
                return
            # check token expiry, e.g. '2019-05-28T10:34:03.240708Z'
            expiry = request.session[f'{provider_type}_expiry']
            if datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S.%fZ") < datetime.utcnow() + timedelta(minutes=1):
                logger.debug('token expiry time is in 1 minute, unauth.')
                unauth(request)
                return

        username = request.session['user']
        providers = {provider_type: get_provider(provider_type, token=request.session.get(f'{provider_type}_token'), user=username)
                     for provider_type in ENABLED_PROVIDERS}
        user = User(username=username, providers=providers)
        return user.auth_credentials, user


async def authenticate(request):
    '''Get user, password from request.form and authenticate with the provider to get a token,
    then set the token to session.
    '''
    from app.config import ENABLED_PROVIDERS
    from app.models.provider import get_provider

    if request.method != 'POST':
        return

    form = await request.form()
    user = form.get('user')
    password = form.get('password')

    tokens, msgs = {}, []
    for provider in ENABLED_PROVIDERS:
        system_provider = get_provider(provider)
        token, msg = system_provider.authenticate(user, password)
        msgs.append(f'{provider} msg: {msg}')
        logger.debug('get token: %s, msg: %s', token, msg)

        if token:
            request.session['user'] = user
            request.session[f'{provider}_token'] = token['token']
            request.session[f'{provider}_expiry'] = token['expiry']
            tokens[provider] = token['token']

    return tokens, ' '.join(msgs)


def unauth(request):
    from app.config import ENABLED_PROVIDERS, AUTH_UNSUPPORT_PROVIDERS

    for provider in ENABLED_PROVIDERS:
        if provider in AUTH_UNSUPPORT_PROVIDERS:
            continue
        request.session.pop(f'{provider}_token', None)
        request.session.pop(f'{provider}_expiry', None)
    return request.session.pop('user', None)
