# coding: utf-8

import logging

from starlette.authentication import (
    AuthenticationBackend,
    AuthCredentials,
    UnauthenticatedUser,
)
from starlette.middleware.base import BaseHTTPMiddleware 

from authlib.jose import jwt
from authlib.jose.errors import JoseError, ExpiredTokenError

from helpdesk.config import OPENID_PRIVIDERS, oauth_username_func
from helpdesk.libs.sentry import report

logger = logging.getLogger(__name__)


# load auth providers
class Validator:
    def __init__(self, metadata_url=None, *args, **kwargs):
        self.metadata_url = metadata_url
        server_metadata_r = requests.get(self.metadata_url)
        server_metadata_r.raise_for_status()
        server_metadata = server_metadata_r.json()

        # Fetch the public key for validating Bearer token
        jwk_r = requests.get(server_metadata['jwks_uri'])
        jwk_r.raise_for_status()
        self.jwk = jwk_r.json()
    
    def valide_token(self, token: str):
        """validate token string, return a parsed token if valid, return None if not valid
        """
        token = jwt.decode(token, self.jwk)
        try:
            token.validate()
            return token
        except ExpiredTokenError as e:
            return None
        except JoseError as e:
            report()
            return None

registed_validator = []

for provider, info in OPENID_PRIVIDERS.items():
    client = Validator(**info)
    registed_validator[provider] = client


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


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        authheader = request.headers.get("Authorization")
        if authheader and authheader.lower().startswith("bearer "):
            _, token_str = authheader.split(" ", 1)
            if token_str:
                for validator in registed_validator:
                    username = oauth_username_func(id_token)
                    email = id_token.get('email', '')
                    roles = []
                    access = id_token.get('resource_access', {})
                    for rs in access.values():
                        roles.extend(rs.get('roles', []))

                    user = User(username, email, roles, id_token.get('picture', ''))

                    request.session['user'] = user.to_json()
        response = await call_next(request)
        return response


def unauth(request):
    return request.session.pop('user', None)
