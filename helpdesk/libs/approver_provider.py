import traceback
from helpdesk.models.db.policy import GroupUser
from helpdesk.models.provider.errors import InitProviderError


class ApproverProvider:
    source = None
        
    async def get_approver_members(self) -> str:
        raise NotImplementedError


class PeopleProvider(ApproverProvider):
    source = "people"

    async def get_approver_members(self, approver):
        return approver


class GroupProvider(ApproverProvider):
    source = "group"

    async def get_approver_members(self, approver):
        group_ids = [int(group_id) for group_id in approver.split(",")]
        members = []
        group_users = await GroupUser.get_all(ids=group_ids)
        if group_users:
            members = [users for approvers in group_users for users in approvers.user_str.split(',')]
        return ",".join(members)


class BridgeProvider(ApproverProvider):
    source = "app"

    async def get_approver_members(self, approver):
        pass


users_providers = {
    'people': PeopleProvider,
    'group': GroupProvider,
    'app': BridgeProvider,
}


def get_approver_provider(provider, **kw):
    try:
        return users_providers[provider](**kw)
    except Exception as e:
        raise InitProviderError(error=e, tb=traceback.format_exc(), description=f"Init provider error: {str(e)}")
