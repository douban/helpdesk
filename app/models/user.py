# coding: utf-8

import logging
from typing import List

from starlette.authentication import BaseUser, AuthCredentials

from app.libs.decorators import cached_property
from app.libs.rest import DictSerializableClassMixin
from app.models.provider import Provider
from app.config import ADMIN_ROLES, avatar_url_func

logger = logging.getLogger(__name__)


class User(DictSerializableClassMixin, BaseUser):
    def __init__(self, username: str, provider: Provider) -> None:
        self.name = username
        self.provider = provider

        self.email = self.provider.get_user_email()

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.name

    @cached_property
    def roles(self) -> List[str]:
        return self.provider.get_user_roles()

    @property
    def is_admin(self) -> bool:
        return any(role in ADMIN_ROLES for role in self.roles)

    @cached_property
    def auth_credentials(self) -> List[str]:
        auths = ["authenticated"]
        auths += ['admin'] if self.is_admin else []
        auths += ['role:' + r for r in self.roles]
        return AuthCredentials(auths)

    @property
    def avatar_url(self) -> str:
        return avatar_url_func(self.name)
