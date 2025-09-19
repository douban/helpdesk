# coding: utf-8

import logging

from helpdesk.config import OPENID_PRIVIDERS

from . import router

logger = logging.getLogger(__name__)


@router.get("/auth/providers")
async def index():
    return list(OPENID_PRIVIDERS.keys())
