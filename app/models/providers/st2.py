# coding: utf-8

import requests

from app.config import (ST2_DEFAULT_PACK, ST2_WORKFLOW_RUNNER_TYPES,
                        ST2_TOKEN_TTL, NO_AUTH_TARGET_OBJECTS,
                        SYSTEM_USER, SYSTEM_USER_PASSWORD)
from app.libs.st2 import (client as service_client,
                          get_client,
                          Execution, Token)
from app.models.provider import Provider


class ST2Provider(Provider):
    provider_type = 'st2'

    def __init__(self, token=None, user=None):
        '''if token is not None, get token client; otherwise get service client
        '''
        super().__init__(token=token, user=user)
        self.st2 = get_client(token) if token else service_client

    def _ref(self, ref):
        if '.' not in ref:
            ref = '.'.join([ST2_DEFAULT_PACK, ref])
        return ref

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
        if ref not in NO_AUTH_TARGET_OBJECTS:
            assert(self.token)

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

    def authenticate(self, user, password=None):
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
            token = token.token
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return token, msg
