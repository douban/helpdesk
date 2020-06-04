# coding: utf-8

import logging
from typing import List, Dict

from starlette.authentication import BaseUser, AuthCredentials

from helpdesk.libs.decorators import cached_property, timed_cache
from helpdesk.libs.rest import DictSerializableClassMixin
from helpdesk.models.provider import Provider
from helpdesk.config import ADMIN_ROLES, avatar_url_func, PROVIDER, AUTH_UNSUPPORT_PROVIDERS

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
        # 对于不支持auth的provider，如果别的provider里有一个role是admin，就视为admin
        if provider_type in AUTH_UNSUPPORT_PROVIDERS:
            for role_list in self.roles.values():
                for role in role_list:
                    if role in ADMIN_ROLES:
                        return True
            return False
        return any(role in ADMIN_ROLES for role in self.roles.get(provider_type, []))

    @cached_property
    def auth_credentials(self) -> List[str]:
        auths = ["authenticated"]
        auths += ['admin'] if self.is_admin(PROVIDER) else []
        auths += ['role:' + r for r in self.roles]
        return AuthCredentials(auths)

    @property
    def avatar_url(self) -> str:
        return avatar_url_func(self.name)
