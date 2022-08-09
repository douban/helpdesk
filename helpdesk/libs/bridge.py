import requests
from helpdesk.config import BRIDGE_URL


class BridgeClient:

    def __init__(self, app_name):
        self.bridge_url = BRIDGE_URL.format(app_name)
        
    def get_maintainer_from_bridge(self):
        res = requests.get(self.bridge_url)
        if res.status_code != 200:
            return None
        return res.json()

    def get_owners(self):
        app_maintainers = self.get_maintainer_from_bridge()
        if app_maintainers:
            return app_maintainers.get('owners', [])
        return []

    def get_release_managers(self):
        app_maintainers = self.get_maintainer_from_bridge()
        if app_maintainers:
            return app_maintainers.get('release_managers', [])
        return []


if __name__ == "__main__":
    app_name = "ban"
    client = BridgeClient(app_name)
    owners = client.get_owners()
    release_manager = client.get_release_managers()

    print(owners)
    print(release_manager)
