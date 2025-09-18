import logging
import traceback
from helpdesk.libs.sentry import report
from helpdesk.models.db.policy import GroupUser
from helpdesk.models.provider.errors import InitProviderError
from helpdesk.config import DEPARTMENT_OWNERS


logger = logging.getLogger(__name__)


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
            members = [
                users
                for approvers in group_users
                for users in approvers.user_str.split(",")
            ]
        return ",".join(members)


class DepartmentProvider(ApproverProvider):
    source = "department"

    async def get_approver_members(self, approver):
        member = DEPARTMENT_OWNERS.get(approver)
        return member or ""


users_providers = {
    "people": PeopleProvider,
    "group": GroupProvider,
    "department": DepartmentProvider,
}


def check_users_providers():
    try:
        from bridge import BridgeOwnerProvider

        users_providers["app_owner"] = BridgeOwnerProvider
    except Exception as e:
        print("check_users_providers:%s", e)
        logger.warning("Get BridgeOwnerProvider error: %s", e)
        report()


def get_approver_provider(provider, **kw):
    check_users_providers()
    try:
        return users_providers[provider](**kw)
    except Exception as e:
        raise InitProviderError(
            error=e,
            tb=traceback.format_exc(),
            description=f"Init provider error: {str(e)}",
        )
