# coding: utf-8

import logging
import requests

from app.config import (ST2_DEFAULT_PACK, ST2_WORKFLOW_RUNNER_TYPES,
                        ST2_TOKEN_TTL, ST2_EXECUTION_RESULT_URL_PATTERN,
                        SYSTEM_USER, SYSTEM_USER_PASSWORD,
                        DEFAULT_EMAIL_DOMAIN)
from app.libs.st2 import (client as service_client,
                          get_client,
                          Execution, Token)
from app.models.provider import Provider
from app.models.providers.ldap import LdapProviderMixin

logger = logging.getLogger(__name__)


class ST2Provider(LdapProviderMixin, Provider):
    provider_type = 'st2'

    def __init__(self, token=None, user=None, api_key=None):
        '''if token is not None, get token client; otherwise get service client
        '''
        super().__init__(token=token, user=user, api_key=api_key)
        # self.st2 is an st2_client instance
        if token or api_key:
            self.st2 = get_client(token, api_key=api_key)
        else:
            self.st2 = service_client

    def get_default_pack(self):
        return ST2_DEFAULT_PACK

    def _ref(self, ref):
        if '.' not in ref:
            ref = '.'.join([ST2_DEFAULT_PACK, ref])
        return ref

    def get_user_email(self, user=None):
        user = user or self.user
        return self.get_user_email_from_ldap(user) or '%s@%s' % (user, DEFAULT_EMAIL_DOMAIN)

    @staticmethod
    def get_result_url(execution_id):
        return ST2_EXECUTION_RESULT_URL_PATTERN.format(execution_id=execution_id)

    def generate_annotation(self, execution):
        return {'provider': self.provider_type, 'id': execution['id'],
                'result_url': self.get_result_url(execution['id'])}

    def get_actions(self, pack=None):
        '''
        return a list of
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        '''
        if pack:
            actions = self.st2.actions.query(pack=pack)
        else:
            actions = self.st2.actions.get_all()
        return [action.to_dict() for action in actions]

    def get_action(self, ref):
        '''
        doc: https://api.stackstorm.com/api/v1/actions/#/actions_controller.get_one

        return
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        '''
        ref = self._ref(ref)
        try:
            action = self.st2.actions.get_by_ref_or_id(ref)
        except TypeError:
            action = None
        return action.to_dict() if action else None

    def run_action(self, ref, parameters):
        ref = self._ref(ref)
        action = self.get_action(ref)
        execution_kwargs = dict(action=ref,
                                action_is_workflow=action['runner_type'] in ST2_WORKFLOW_RUNNER_TYPES,
                                parameters=parameters)
        execution = None
        msg = ''
        try:
            execution = self.st2.executions.create(Execution(**execution_kwargs))
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return (execution.to_dict() if execution else None, msg)

    def get_execution(self, execution_id):
        execution = None
        msg = ''
        try:
            execution = self.st2.executions.get_by_id(execution_id)
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return (execution.to_dict() if execution else None, msg)

    def authenticate(self, user, password=None):
        ''' return a token dict and msg.

        st2 POST /auth/v1/tokens, returns
        {'service': False, 'expiry': '2019-05-28T10:34:03.240708Z', 'token': '48951e681dd64b4380a19998d6ec655e',
         'user': 'xxx', 'id': '5cebbd1b7865303ddd77d503', 'metadata': {}}
        '''
        token_kw = dict(ttl=ST2_TOKEN_TTL)
        if password:
            kw = dict(auth=(user, password))
        else:
            # if no password, use service account to request impersonated tokens
            kw = dict(auth=(SYSTEM_USER, SYSTEM_USER_PASSWORD))
            token_kw['user'] = user

        token = None
        msg = ''
        try:
            token = self.st2.tokens.create(Token(**token_kw), **kw)
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return token.to_dict() if token else None, msg

    def get_user_roles(self, user=None):
        '''return a list of roles,
            e.g. ["admin"]

        st2 GET /api/v1/user, returns

        {
            "username": "xxx",
            "rbac": {
                "is_admin": true,
                "enabled": true,
                "roles": [
                    "admin"
                ]
            },
            "authentication": {
                "token_expire": "2019-05-25T06:03:47Z",
                "method": "authentication token",
                "location": "header"
            },
            "impersonate": {
                "nicknames": {
                    "slack": "xxx"
                },
                "is_service": false
            }
        }
        '''
        user_info = self.st2.get_user_info()
        roles = user_info.get('rbac', {}).get('roles', [])
        logger.debug('Get user roles: %s.get_user_roles(): %s', self, roles)
        return roles
