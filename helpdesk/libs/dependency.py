# coding: utf-8

import logging

from starlette import status
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from helpdesk.config import oauth_username_func
from helpdesk.models.user import User

logger = logging.getLogger(__name__)


def get_current_user(request: Request):
    userinfo = request.session.get("user")
    if not userinfo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = User.parse_raw(userinfo)
    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.roles:
        if "admin" in user.roles:
            return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
    )
