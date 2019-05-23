# coding: utf-8

import logging

from starlette.authentication import BaseUser

logger = logging.getLogger(__name__)


class User(BaseUser):
    def __init__(self, username: str) -> None:
        self.username = username

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username
