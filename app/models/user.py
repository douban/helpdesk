# coding: utf-8

import logging
from typing import List

from starlette.authentication import BaseUser

from app.libs.rest import DictSerializableClassMixin
from app.config import avatar_url_func

logger = logging.getLogger(__name__)


class User(DictSerializableClassMixin, BaseUser):
    def __init__(self, username: str, auths: List[str] = None) -> None:
        self.username = username
        self.auths = auths

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username

    @property
    def is_admin(self) -> bool:
        return 'admin' in self.auths

    @property
    def roles(self) -> List[str]:
        return [a[len('role:'):] for a in self.auths]

    @property
    def avatar_url(self) -> str:
        return avatar_url_func(self.display_name)
