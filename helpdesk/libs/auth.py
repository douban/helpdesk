# coding: utf-8

import logging

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
        logger.debug('request.session: %s, user: %s', request.session, request.session.get('user'))
        username = request.session.get('user')
        email = request.session.get('email')
        roles = request.session.get('roles', '').split(",")

        if not username or not email:
            return AuthCredentials([]), UnauthenticatedUser()

        user = User(username=username, email=email, roles=roles)
        return user.auth_credentials, user


def unauth(request):
    return request.session.pop('user', None)
