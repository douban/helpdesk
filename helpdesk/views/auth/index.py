import logging

from starlette.authentication import requires, has_required_scope  # NOQA
from authlib.integrations.starlette_client import OAuth

from . import bp

logger = logging.getLogger(__name__)

oauth = OAuth()

oauth.register(
    'google',
    client_id='...',
    client_secret='...',
)


@bp.route('/{provider}', methods=['GET'])
async def login(request):
    provider = request.path_params.get('provider', '')
    client = oauth.create_client(provider)
    redirect_uri = request.url_for('authorize')
    return await client.authorize_redirect(request, redirect_uri)


    # token, msg = await authenticate(request)
    # return {'success': bool(token), 'msg': msg, 'token': token}

@app.route('/auth/{provider}/callback')
async def authorize(request):
    provider = request.path_params.get('provider', '')
    client = oauth.create_client(provider)

    token = await client.authorize_access_token(request)
    user = await client.parse_id_token(request, token)
    # do something with the token and profile
    return '...'

@bp.route('/logout', methods=['POST'])
@requires(['authenticated'])
async def logout(request):
    # unauth(request)
    return {'success': True, 'msg': ''}
