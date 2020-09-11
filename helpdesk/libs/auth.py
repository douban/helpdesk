# coding: utf-8

import logging

import requests
from starlette.authentication import (
    AuthenticationBackend,
    AuthCredentials,
    UnauthenticatedUser,
)
from starlette.middleware.base import BaseHTTPMiddleware
from authlib.jose import jwt
from authlib.jose.errors import JoseError, ExpiredTokenError, DecodeError

from helpdesk.config import OPENID_PRIVIDERS, oauth_username_func
from helpdesk.libs.sentry import report
from helpdesk.models.user import User

logger = logging.getLogger(__name__)


# load auth providers
class Validator:
    def __init__(self, metadata_url=None, client_id=None, *args, **kwargs):
        self.metadata_url = metadata_url
        self.client_id = client_id
        if not self.client_id:
            raise ValueError('Init validator failed, client_id not set')
        self.client_kwargs = kwargs.get('client_kwargs')
        self.fetch_jwk()

    def fetch_jwk(self):
        # Fetch the public key for validating Bearer token
        server_metadata = self.get(self.metadata_url)
        self.jwk = self.get(server_metadata['jwks_uri'])

    def get(self, *args, **kwargs):
        if self.client_kwargs:
            r = requests.get(*args, **kwargs, **self.client_kwargs)
        else:
            r = requests.get(*args, **kwargs)
        r.raise_for_status()
        return r.json()

    def valide_token(self, token: str):
        """validate token string, return a parsed token if valid, return None if not valid
        :return tuple (is_token -> bool, id_token or None)
        The BearerAuthMiddleware would use this to decide if we should validate the token in the next provider.
        If is_token == True, but id_token is None, that means the token is some kind of valid
        but not accepted by the current provider, so the middleware will try anther one.
        If is_token != True, that means the token is expired, not valid or something occurs during decoding.
        The middleware would give up trying other providers
        """
        try:
            if "https://accounts.google.com" in self.metadata_url:
                # google's certs would change from time to time, let's refetch it before every try
                self.fetch_jwk()
            token = jwt.decode(token, self.jwk)
        except ValueError as e:
            if str(e) == 'Invalid JWK kid':
                logger.info(
                    'This token cannot be decoded with current provider, will try another provider if available.')
                return True, None
            else:
                report()
                return False, None
        except DecodeError as e:
            logger.info("Token decode failed: %s", str(e))
            return False, None

        try:
            token.validate()
            return True, token
        except ExpiredTokenError as e:
            logger.info('Auth header expired, %s', e)
            return False, None
        except JoseError as e:
            logger.debug('Jose error: %s', e)
            report()
            return False, None


registed_validator = {}

for provider, info in OPENID_PRIVIDERS.items():
    client = Validator(metadata_url=info['server_metadata_url'], **info)
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
                for validator_name, validator in registed_validator.items():
                    logger.info("Trying to validate token with %s", validator_name)
                    is_token, id_token = validator.valide_token(token_str)
                    if not is_token:
                        break
                    if is_token and not id_token:
                        # not valid in this provider, try next
                        continue
                    # check aud and iss
                    aud = id_token.get('aud')
                    if id_token.get('azp') != validator.client_id and (not aud or validator.client_id not in aud):
                        logger.info('Token is valid, not expired, but not belonged to this client')
                        break
                    logger.info("Validate token with %s success", validator_name)
                    username = oauth_username_func(id_token)
                    email = id_token.get('email', '')
                    access = id_token.get('resource_access', {})
                    roles = access.get(validator.client_id, {}).get('roles', [])

                    user = User(username, email, roles, id_token.get('picture', ''))

                    request.session['user'] = user.to_json()
                    break
        response = await call_next(request)
        return response


def unauth(request):
    return request.session.pop('user', None)
