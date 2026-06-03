import requests


class DataClient:
    BASE_URL = "Override BASE_URL in child class for using API"

    def __init__(self, api_token: str = None, timeout: int = 30):
        self.api_token = api_token
        self.timeout = timeout
        self.headers = {}

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()