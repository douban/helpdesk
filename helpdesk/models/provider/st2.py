# coding: utf-8

import logging
import requests
import traceback

from helpdesk.config import (
    ST2_DEFAULT_PACK,
    ST2_WORKFLOW_RUNNER_TYPES,
    ST2_TOKEN_TTL,
    ST2_BASE_URL,
    ST2_EXECUTION_RESULT_URL_PATTERN,
    ST2_USERNAME,
    ST2_PASSWORD,
)
from helpdesk.libs.sentry import report
from helpdesk.libs.st2 import get_client, get_api_client, Execution, Token
from helpdesk.models.provider.errors import ResolvePackageError

from .base import BaseProvider

logger = logging.getLogger(__name__)


class ST2Provider(BaseProvider):
    provider_type = 'st2'

    def __init__(self, token=None, **kwargs):
        '''if token is not None, get token client; otherwise get service client
        '''
        super().__init__(**kwargs)
        self.base_url = ST2_BASE_URL
        if not token:
            token = self._get_token()

        # self.st2 is an st2_client instance
        self.st2 = get_client(token)

    def get_default_pack(self):
        return ST2_DEFAULT_PACK

    def _ref(self, ref):
        if '.' not in ref:
            ref = '.'.join([ST2_DEFAULT_PACK, ref])
        return ref

    def get_result_url(self, execution_id):
        return ST2_EXECUTION_RESULT_URL_PATTERN.format(base_url=self.base_url, execution_id=execution_id)

    def generate_annotation(self, execution):
        if not execution:
            return
        return {
            'provider': self.provider_type,
            'id': execution['id'],
            'result_url': self.get_result_url(execution['id'])
        }

    def get_actions(self, pack=None):
        '''
        return a list of
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        '''
        if pack:
            try:
                actions = self.st2.actions.query(pack=pack)
            except Exception as e:
                raise ResolvePackageError(e, traceback.format_exc(), f"Resolve pack {pack} error")
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
        execution_kwargs = dict(
            action=ref, action_is_workflow=action['runner_type'] in ST2_WORKFLOW_RUNNER_TYPES, parameters=parameters)
        execution = None
        msg = ''
        try:
            execution = self.st2.executions.create(Execution(**execution_kwargs))
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return execution.to_dict() if execution else None, msg

    def get_execution(self, execution_id):
        execution = None
        msg = ''
        try:
            execution = self.st2.executions.get_by_id(execution_id)
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return execution.to_dict() if execution else None, msg

    def _get_token(self):
        ''' return a token dict and msg.

        st2 POST /auth/v1/tokens, returns
        {'service': False, 'expiry': '2019-05-28T10:34:03.240708Z', 'token': '48951e681dd64b4380a19998d6ec655e',
         'user': 'xxx', 'id': '5cebbd1b7865303ddd77d503', 'metadata': {}}
        '''
        token = None
        try:
            token = get_api_client().tokens.create(
                Token(ttl=ST2_TOKEN_TTL),
                auth=(ST2_USERNAME, ST2_PASSWORD),
            )
        except requests.exceptions.HTTPError as e:
            logger.error('get st2 token error: %s', e)
            report()
        return token.token if token else None
