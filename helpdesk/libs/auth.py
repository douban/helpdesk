# coding: utf-8

import logging
from datetime import datetime, timedelta

from starlette.authentication import (
    AuthenticationBackend,
    AuthCredentials,
    UnauthenticatedUser,
)

logger = logging.getLogger(__name__)

# ref: https://www.starlette.io/authentication/


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        from helpdesk.models.user import User
        from helpdesk.models.provider import get_provider
        from helpdesk.config import ENABLED_PROVIDERS
        logger.debug('request.session: %s, user: %s', request.session, request.session.get('user'))

        for provider_type in ENABLED_PROVIDERS:
            # if provider_type in AUTH_UNSUPPORT_PROVIDERS:
            #     continue
            if not all([request.session.get('user'), request.session.get(f'{provider_type}_token'),
                        request.session.get(f'{provider_type}_expiry')]):
                logger.debug(f'{provider_type} auth error, unauth')
                return AuthCredentials([]), UnauthenticatedUser()
            # check token expiry, e.g. '2019-05-28T10:34:03.240708Z'
            expiry = request.session[f'{provider_type}_expiry']
            if datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S.%fZ") < datetime.utcnow() + timedelta(minutes=1):
                logger.debug('token expiry time is in 1 minute, unauth.')
                unauth(request)
                return AuthCredentials([]), UnauthenticatedUser()

        username = request.session['user']
        providers = {
            provider_type:
            get_provider(provider_type, token=request.session.get(f'{provider_type}_token'), user=username)
            for provider_type in ENABLED_PROVIDERS
        }
        user = User(username=username, providers=providers)
        return user.auth_credentials, user


async def authenticate(request):
    '''Get user, password from request.form and authenticate with the provider to get a token,
    then set the token to session.
    '''
    from helpdesk.config import ENABLED_PROVIDERS
    from helpdesk.models.provider import get_provider

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
    from helpdesk.config import ENABLED_PROVIDERS, AUTH_UNSUPPORT_PROVIDERS

    for provider in ENABLED_PROVIDERS:
        if provider in AUTH_UNSUPPORT_PROVIDERS:
            continue
        request.session.pop(f'{provider}_token', None)
        request.session.pop(f'{provider}_expiry', None)
    return request.session.pop('user', None)
