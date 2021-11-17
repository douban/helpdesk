# coding: utf-8

import logging
from typing import List
from pydantic import BaseModel, validator


from helpdesk.config import ADMIN_ROLES, AUTHORIZED_EMAIL_DOMAINS, avatar_url_func

logger = logging.getLogger(__name__)


class User(BaseModel):
    name: str
    email: str
    roles: List[str] = []
    avatar: str = None

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def is_admin(self) -> bool:
        return any(role in ADMIN_ROLES for role in self.roles)

    @validator('email')
    def validate_email(cls, v):
        if not v:
            return v
        for suffix in AUTHORIZED_EMAIL_DOMAINS:
            if v.endswith(suffix):
                return v
        raise ValueError("email domain illegal, not inside allowed domains")

    @validator('avatar')
    def set_defaults_avatar(cls, v, values):
        if not v and values.get('email'):
            return avatar_url_func(values['email'])
        return v
