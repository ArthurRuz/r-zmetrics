from integrations.clients.clients_utils import handle_api_errors
from integrations.clients.data_client import DataClient


class APIFootballClient(DataClient):
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_token: str, timeout: int = 30):
        super().__init__(api_token, timeout)
        self.headers = {
            "X-Auth-Token": self.api_token
        }

    @handle_api_errors()
    def get_leagues(self) -> dict:
        return self._get('/leagues')

    @handle_api_errors()
    def get_teams(self, **kwargs) -> dict:
        return self._get('/teams', kwargs)