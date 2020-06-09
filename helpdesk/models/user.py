# coding: utf-8

import logging
from typing import List

from starlette.authentication import BaseUser, AuthCredentials

from helpdesk.libs.decorators import cached_property
from helpdesk.libs.rest import DictSerializableClassMixin
from helpdesk.config import ADMIN_ROLES, avatar_url_func

logger = logging.getLogger(__name__)


class User(DictSerializableClassMixin, BaseUser):
    def __init__(self, username: str, email: str, roles: list) -> None:
        self.name = username
        self.email = email
        self.roles = roles

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.name

    @cached_property
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
