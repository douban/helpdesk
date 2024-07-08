import logging

from starlette.responses import HTMLResponse
from starlette.authentication import requires, has_required_scope  # NOQA
from authlib.integrations.starlette_client import OAuth

from fastapi import Request

from helpdesk.config import OPENID_PRIVIDERS, oauth_username_func, DEFAULT_BASE_URL
from helpdesk.models.user import User

from . import router

logger = logging.getLogger(__name__)

oauth_clients = {}

for provider, info in OPENID_PRIVIDERS.items():
    _auth = OAuth()
    _auth.register(provider, **info)
    client = _auth.create_client(provider)
    oauth_clients[provider] = client


@router.get('/oauth/{oauth_provider}')
async def oauth(request: Request):

    oauth_provider = request.path_params.get('oauth_provider', '')
    oauth_client = oauth_clients[oauth_provider]

    # FIXME: url_for behind proxy
    url_path = request.app.router.url_path_for('callback', oauth_provider=oauth_provider)
    redirect_uri = url_path.make_absolute_url(base_url=DEFAULT_BASE_URL)

    return await oauth_client.authorize_redirect(request, str(redirect_uri))


@router.get('/callback/{oauth_provider}')
async def callback(oauth_provider: str, request: Request):
    oauth_client = oauth_clients[oauth_provider]

    token = await oauth_client.authorize_access_token(request)
    userinfo = token['userinfo']
    logger.debug("auth succeed %s", userinfo)

    username = oauth_username_func(userinfo)
    email = userinfo['email']

    access = userinfo.get('resource_access', {})
    roles = access.get(oauth_client.client_id, {}).get('roles', [])

    user = User(name=username, email=email, roles=roles, avatar=userinfo.get('picture', ''))

    request.session['user'] = user.json()

    return HTMLResponse("<script>window.close()</script>", 200)


@router.post('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return {'success': True, 'msg': ''}
