import logging

from starlette.responses import JSONResponse
from starlette.authentication import requires, has_required_scope  # NOQA
from authlib.integrations.starlette_client import OAuth

from helpdesk.config import OPENID_PRIVIDERS

from . import bp

logger = logging.getLogger(__name__)


oauth_clients = {}

for provider, info in OPENID_PRIVIDERS.items():
    _auth = OAuth()
    _auth.register(provider, **info)
    client = _auth.create_client(provider)
    oauth_clients[provider] = client


@bp.route('/oauth/{provider}', methods=['GET'])
async def oauth(request):
    provider = request.path_params.get('provider', '')
    client = oauth_clients[provider]

    redirect_uri = request.url_for('auth:callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)


@bp.route('/callback/{provider}')
async def callback(request):
    provider = request.path_params.get('provider', '')
    client = oauth_clients[provider]

    token = await client.authorize_access_token(request)
    user = await client.parse_id_token(request, token)
    logger.debug("auth succeed %s", user)

    request.session['user'] = user['preferred_username']
    request.session['email'] = user['email']
    roles = []
    access = user.get('resource_access', {})
    for rs in access.values():
        roles.extend(rs.get('roles', []))
    request.session['roles'] = ','.join(roles)
    return JSONResponse(user, 200)


@bp.route('/logout', methods=['POST'])
@requires(['authenticated'])
async def logout(request):
    # unauth(request)
    return {'success': True, 'msg': ''}
