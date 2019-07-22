import logging

from starlette.authentication import requires, has_required_scope  # NOQA

from . import bp
from app.libs.rest import jsonize
from app.libs.auth import authenticate, unauth

logger = logging.getLogger(__name__)


@bp.route('/auth/login', methods=['POST'])
@jsonize
async def challenge(request):
    token, msg = await authenticate(request)

    if token:
        return {'success': True, 'msg': msg, 'token': token}
    return {'success': False, 'msg': msg, 'token': ''}


@bp.route('/auth/logout', methods=['POST'])
@requires(['authenticated'])
@jsonize
async def revoke(request):
    unauth(request)
    return {'success': True, 'msg': ''}


@bp.route('/auth/heartbeat', methods=['GET'])
@requires(['authenticated'])
@jsonize
async def heartbeat(request):
    return {'status_code': 200, 'msg':'OK'}
