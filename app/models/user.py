# coding: utf-8

import logging
from typing import List, Dict

from starlette.authentication import BaseUser, AuthCredentials

from app.libs.decorators import cached_property, timed_cache
from app.libs.rest import DictSerializableClassMixin
from app.models.provider import Provider
from app.config import ADMIN_ROLES, avatar_url_func, PROVIDER

logger = logging.getLogger(__name__)


class User(DictSerializableClassMixin, BaseUser):
    def __init__(self, username: str, providers: Dict[str, Provider]) -> None:
        self.name = username
        self.providers = providers

        self.email = self.providers[PROVIDER].get_user_email()

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.name

    @cached_property
    def roles(self) -> Dict[str, List[str]]:
        return {provider_type: provider.get_user_roles() for provider_type, provider in self.providers.items()}

    @timed_cache(seconds=300)
    def is_admin(self, provider_type) -> bool:
        return any(role in ADMIN_ROLES for role in self.roles[provider_type])

    @cached_property
    def auth_credentials(self) -> List[str]:
        auths = ["authenticated"]
        auths += ['admin'] if self.is_admin(PROVIDER) else []
        auths += ['role:' + r for r in self.roles]
        return AuthCredentials(auths)

    @property
    def avatar_url(self) -> str:
        return avatar_url_func(self.name)
