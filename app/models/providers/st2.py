# coding: utf-8


from app.config import ST2_DEFAULT_PACK
from app.libs.st2 import client as st2
from app.models.provider import Provider


class ST2Provider(Provider):
    def __init__(self):
        pass

    def get_actions(self, pack=None):
        '''
        return a list of
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        '''
        if pack:
            actions = st2.actions.query(pack=pack)
        else:
            actions = st2.actions.get_all()
        return [action.to_dict() for action in actions]

    def get_action(self, ref):
        '''
        doc: https://api.stackstorm.com/api/v1/actions/#/actions_controller.get_one

        return
        <Action name=view_organizations,pack=trello,enabled=True,runner_type=python-script>
        to dict
        '''
        if '.' not in ref:
            ref = '.'.join([ST2_DEFAULT_PACK, ref])
        try:
            action = st2.actions.get_by_ref_or_id(ref)
        except TypeError:
            action = None
        return action.to_dict() if action else None
