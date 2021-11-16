
# coding: utf-8

import logging

import requests

from authlib.jose import jwt
from authlib.jose.errors import JoseError, ExpiredTokenError, DecodeError
from starlette import status
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from helpdesk.config import OPENID_PROVIDER, oauth_username_func
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
        self.server_metadata = {}
        self.jwk = {}
        self.token_endpoint = ""
        self.authorization_endpoint = ""

    def fetch_configs(self):
        # Fetch the public key for validating Bearer token
        self.server_metadata = self.get(self.metadata_url)
        self.jwk = self.get(self.server_metadata['jwks_uri'])
        self.token_endpoint = self.server_metadata['token_endpoint']
        self.authorization_endpoint = self.server_metadata['authorization_endpoint']

    def get(self, *args, **kwargs):
        if self.client_kwargs:
            r = requests.get(*args, **kwargs, **self.client_kwargs)
        else:
            r = requests.get(*args, **kwargs)
        r.raise_for_status()
        return r.json()

    def valide_token(self, token: str):
        """validate token string, return a parsed token if valid, return None if not valid
        :return tuple (is_valid -> bool, id_token or None)
        """
        try:
            if "https://accounts.google.com" in self.metadata_url:
                # google's certs would change from time to time, let's refetch it before every try
                self.fetch_configs()
            token = jwt.decode(token, self.jwk)
        except ValueError as e:
            if str(e) == 'Invalid JWK kid':
                logger.info(
                    'This token cannot be decoded with current provider')
                return None, None
            else:
                raise e
        except DecodeError as e:
            logger.info("Token decode failed: %s", str(e))
            return False, None

        try:
            token.validate()
            return True, token
        except ExpiredTokenError as e:
            logger.info('Auth header expired, %s', e)
            return True, None
        except JoseError as e:
            logger.error('Jose error: %s', e)
            return None, None

    def parse_token(self, token: str) -> User or None:
        logger.info("Trying to validate token with %s", self.metadata_url)
        valid, id_token = self.valide_token(token)
        if not id_token:
            # not valid
            return
        # check aud and iss
        aud = id_token.get('aud')
        if id_token.get('azp') != self.client_id and (not aud or self.client_id not in aud):
            logger.info('Token is valid, not expired, but not belonged to this client')
            return
        username = oauth_username_func(id_token)
        email = id_token.get('email', '')
        access = id_token.get('resource_access', {})
        app_roles = access.get(self.client_id, {"roles": []})

        user = User(name=username, email=email, roles=app_roles["roles"], avatar=id_token.get('picture', ''))

        return user


registered_validator = Validator(metadata_url=OPENID_PROVIDER['server_metadata_url'], **OPENID_PROVIDER)


registered_validator.fetch_configs()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=registered_validator.token_endpoint)


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = registered_validator.parse_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.roles:
        if 'admin' in user.roles:
            return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")