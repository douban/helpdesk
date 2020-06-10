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
        userinfo = request.session.get('user')
        if not userinfo:
            return AuthCredentials([]), UnauthenticatedUser()

        try:
            user = User.from_json(userinfo)
            return user.auth_credentials, user
        except Exception:
            return AuthCredentials([]), UnauthenticatedUser()


def unauth(request):
    return request.session.pop('user', None)
