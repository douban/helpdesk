# coding: utf-8

import requests

from app.config import (ST2_DEFAULT_PACK, ST2_WORKFLOW_RUNNER_TYPES,
                        ST2_TOKEN_TTL, NO_AUTH_TARGET_OBJECTS)
from app.libs.st2 import (client as service_client,
                          get_client,
                          Execution, Token)
from app.models.provider import Provider


class ST2Provider(Provider):
    def __init__(self, token=None):
        super().__init__(token=token)
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
        execution = self.st2.executions.create(Execution(**execution_kwargs))
        return execution.to_dict() if execution else None

    def authenticate(self, user, password):
        kwargs = dict(ttl=ST2_TOKEN_TTL)
        token = None
        msg = ''
        try:
            token = self.st2.tokens.create(Token(**kwargs), auth=(user, password))
            token = token.token
        except requests.exceptions.HTTPError as e:
            msg = str(e)
        return token, msg
