from integrations.clients.clients_utils import handle_api_errors
from integrations.clients.data_client import DataClient


class TheSportsDbClient(DataClient):
    BASE_URL = "https://www.thesportsdb.com/api/v1/json"

    def __init__(self, api_token: str, timeout: int = 30):
        super().__init__(api_token, timeout)
        TheSportsDbClient.BASE_URL += f'/{api_token}'

    @handle_api_errors()
    def get_player_by_name(self, player_name: str) -> dict:
        return self._get('/searchplayers.php', {'p': player_name})

    @handle_api_errors()
    def get_player_by_id(self, player_id: int) -> dict:
        return self._get('/lookupplayer.php', {'id': player_id})

    @handle_api_errors()
    def get_stadium_by_name(self, stadium_name: str) -> dict:
        return self._get('/searchvenues.php', {'v': stadium_name})
