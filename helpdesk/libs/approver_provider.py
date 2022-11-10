import traceback
from helpdesk.models.db.policy import GroupUser
from helpdesk.models.provider.errors import InitProviderError
from helpdesk.config import DEPARTMENT_OWNERS


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
        members = []
        group_users = await GroupUser.get_by_group_name(group_name=approver)
        if group_users:
            members = [users for approvers in group_users for users in approvers.user_str.split(',')]
        return ",".join(members)


class DepartmentProvider(ApproverProvider):
    source = "department"

    async def get_approver_members(self, approver):
        member = DEPARTMENT_OWNERS.get(approver)
        return member or ""


from bridge import BridgeOwnerProvider
users_providers = {
    'people': PeopleProvider,
    'group': GroupProvider,
    'app_owner': BridgeOwnerProvider,
    'department': DepartmentProvider,
}


def get_approver_provider(provider, **kw):
    try:
        return users_providers[provider](**kw)
    except Exception as e:
        raise InitProviderError(error=e, tb=traceback.format_exc(), description=f"Init provider error: {str(e)}")
