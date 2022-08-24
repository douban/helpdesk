import requests
from helpdesk.libs.approver_provider import ApproverProvider


class BridgeOwnerProvider(ApproverProvider):
    source = "app_owner"
    bridge_url = 'https://bridge.dapps.douban.com/api/app/{}/contacts'

    async def get_approver_members(self, approver):
        res = requests.get(self.bridge_url.format(approver))
        if res.status_code != 200:
            return ""
        owners = res.json().get('owners', [])
        return ",".join(owners)


if __name__ == "__main__":
    app_name = "ban"
    bridge_client = BridgeOwnerProvider()
    owners = bridge_client.get_approver_members(app_name)
    print(owners)
