# coding: utf-8

import logging

from helpdesk.libs.rest import jsonize
from helpdesk.config import OPENID_PRIVIDERS

from . import bp

logger = logging.getLogger(__name__)


@bp.route('/auth/providers')
@jsonize
async def index(request):
    return list(OPENID_PRIVIDERS.keys())
