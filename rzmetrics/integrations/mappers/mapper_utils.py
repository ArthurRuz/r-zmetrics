from datetime import datetime


def parse_datetime(value: str | None):
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))