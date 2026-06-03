from integrations.clients.clients_utils import handle_api_errors
from integrations.clients.data_client import DataClient


class FootballDataClient(DataClient):
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_token: str, timeout: int = 30):
        super().__init__(api_token, timeout)
        self.headers = {
            "X-Auth-Token": self.api_token
        }

    @handle_api_errors()
    def get_countries(self) -> dict:
        return self._get("/areas")

    @handle_api_errors()
    def get_competitions(self) -> dict:
        return self._get("/competitions")

    @handle_api_errors()
    def get_competition_seasons(self, competition: str) -> dict:
        return self._get(f"/competitions/{competition}")

    @handle_api_errors()
    def get_teams_by_competition(self, competition: str, season: int = 2025) -> dict:
        return self._get(f"/competitions/{competition}/teams", {"season": season})

    @handle_api_errors()
    def get_team_by_id(self, id: int, season: int = 2025) -> dict:
        return self._get(f"/teams/{id}", {"season": season})

    @handle_api_errors()
    def get_matches_by_competition(self, competition: str, season = 2025) -> dict:
        return self._get(f"/competitions/{competition}/matches", {"season": season})

    @handle_api_errors()
    def get_player_by_id(self, id: int) -> dict:
        return self._get(f"/persons/{id}")

    @handle_api_errors()
    def get_competition_standings(self, competition: str, season: int = 2025) -> dict:
        return self._get(f"/competitions/{competition}/standings", {"season": season})