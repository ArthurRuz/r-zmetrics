import json


class SofaScoreClient:
    BASE_URL = "https://www.sofascore.com/api/v1"

    def __init__(self, esd_client):
        self.esd_client = esd_client

    def get_event_lineups(self, event_id: int) -> dict:
        service = self.esd_client._SofascoreClient__service

        url = f"{self.BASE_URL}/event/{event_id}/lineups"
        service.page.goto(url, wait_until="networkidle")

        text = service.page.locator("body").inner_text()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Не удалось распарсить SofaScore lineups JSON для event_id={event_id}. "
                f"Ответ: {text[:500]}"
            ) from e

    def get_event(self, event_id: int) -> dict:
        service = self.esd_client._SofascoreClient__service

        url = f"{self.BASE_URL}/event/{event_id}"
        service.page.goto(url, wait_until="networkidle")

        text = service.page.locator("body").inner_text()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Не удалось распарсить SofaScore event JSON для event_id={event_id}. "
                f"Ответ: {text[:500]}"
            ) from e