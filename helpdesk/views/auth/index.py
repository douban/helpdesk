import logging

from starlette.responses import HTMLResponse
from starlette.authentication import requires, has_required_scope  # NOQA
from authlib.integrations.starlette_client import OAuth

from helpdesk.config import OPENID_PRIVIDERS
from helpdesk.models.user import User
from helpdesk.libs.rest import jsonize

from . import bp

logger = logging.getLogger(__name__)

oauth_clients = {}

for provider, info in OPENID_PRIVIDERS.items():
    _auth = OAuth()
    _auth.register(provider, **info)
    client = _auth.create_client(provider)
    oauth_clients[provider] = client


@bp.route('/oauth/{provider}')
async def oauth(request):
    provider = request.path_params.get('provider', '')
    client = oauth_clients[provider]

    # FIXME: url_for behind proxy
    url_path = request['router'].url_path_for('auth:callback', provider=provider)
    server = request["server"]
    base_url = f"{request['scheme']}://{server[0]}:{server[1]}{request.get('app_root_path', '/')}"
    redirect_uri = url_path.make_absolute_url(base_url=base_url)

    return await client.authorize_redirect(request, redirect_uri)


@bp.route('/callback/{provider}')
async def callback(request):
    provider = request.path_params.get('provider', '')
    client = oauth_clients[provider]

    token = await client.authorize_access_token(request)
    id_token = await client.parse_id_token(request, token)
    logger.debug("auth succeed %s", id_token)

    username = id_token['name']
    email = id_token['email']
    if not User.validate_email(email):
        return HTMLResponse("invalid email", 403)

    roles = []
    access = id_token.get('resource_access', {})
    for rs in access.values():
        roles.extend(rs.get('roles', []))

    user = User(username, email, roles, id_token.get('picture', ''))

    request.session['user'] = user.to_json()

    return HTMLResponse("<script>window.close()</script>", 200)


@bp.route('/logout', methods=['POST'])
@requires(['authenticated'])
@jsonize
async def logout(request):
    request.session.pop('user', None)
    return {'success': True, 'msg': ''}
