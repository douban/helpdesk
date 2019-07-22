import logging

from starlette.authentication import requires, has_required_scope  # NOQA

from . import bp
from app.libs.rest import jsonize
from app.libs.auth import authenticate, unauth

logger = logging.getLogger(__name__)


@bp.route('/auth/login', methods=['POST'])
@jsonize
async def login(request):
    token, msg = await authenticate(request)
    return {'success': bool(token), 'msg' :msg, 'token': token}


@bp.route('/auth/logout', methods=['POST'])
@requires(['authenticated'])
@jsonize
async def logout(request):
    unauth(request)
    return {'success': True, 'msg': ''}
