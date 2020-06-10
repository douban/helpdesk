# coding: utf-8

import json
import logging
from typing import List

from starlette.authentication import BaseUser, AuthCredentials

from helpdesk.libs.decorators import cached_property
from helpdesk.libs.rest import DictSerializableClassMixin
from helpdesk.config import ADMIN_ROLES, AUTHORIZED_EMAIL_DOMAINS, avatar_url_func

logger = logging.getLogger(__name__)


class User(DictSerializableClassMixin, BaseUser):
    def __init__(self, name: str, email: str, roles: list, avatar: str) -> None:
        self.name = name
        self.email = email
        self.roles = roles
        self.avatar = avatar if avatar else avatar_url_func(self.email)

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

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, info: str) -> object:
        _info = json.loads(info)
        return cls(_info['name'], _info['email'], _info['roles'], _info['avatar'])

    @classmethod
    def validate_email(cls, email: str) -> bool:
        for suffix in AUTHORIZED_EMAIL_DOMAINS:
            if email.endswith(suffix):
                return True
        return False
