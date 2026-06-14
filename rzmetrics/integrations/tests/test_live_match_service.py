import sys
from unittest.mock import MagicMock

# Тяжёлые зависимости (Playwright, ESD) не нужны для unit-тестов маппинга статусов и счёта.
sys.modules.setdefault("esd", MagicMock())
sys.modules.setdefault(
    "integrations.services.matches_parser",
    MagicMock(update_single_match_details=MagicMock()),
)
sys.modules.setdefault(
    "integrations.services.sofascore_worker",
    MagicMock(run_in_playwright_thread=MagicMock()),
)

import pytest

from football.models import Match
from integrations.services.live_match_service import (
    map_sofascore_status,
    update_match_score_from_sofascore,
)


@pytest.mark.parametrize(
    "status_data,expected",
    [
        ({"type": "notstarted"}, Match.Status.TIMED),
        ({"type": "finished"}, Match.Status.FINISHED),
        ({"type": "postponed"}, Match.Status.POSTPONED),
        ({"type": "canceled"}, Match.Status.CANCELLED),
        ({"type": "cancelled"}, Match.Status.CANCELLED),
        ({"type": "interrupted"}, Match.Status.PAUSED),
        ({"type": "unknown"}, None),
    ],
)
def test_map_sofascore_status_basic(status_data, expected):
    assert map_sofascore_status(status_data) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        ("halftime", Match.Status.PAUSED),
        ("half time", Match.Status.PAUSED),
        ("break", Match.Status.PAUSED),
        ("1st half", Match.Status.IN_PLAY),
        ("2nd half", Match.Status.IN_PLAY),
        ("extra time 1st half", Match.Status.EXTRA_TIME),
        ("penalty shootout", Match.Status.PENALTY_SHOOTOUT),
        ("live", Match.Status.IN_PLAY),
    ],
)
def test_map_sofascore_status_inprogress(description, expected):
    status_data = {"type": "inprogress", "description": description}
    assert map_sofascore_status(status_data) == expected


@pytest.mark.django_db
def test_update_match_score_from_sofascore(competition_season, home_team, away_team):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime="2025-09-01T15:00:00Z",
        status=Match.Status.IN_PLAY,
    )

    event_data = {
        "homeScore": {
            "current": 2,
            "period1": 1,
            "period2": 1,
            "period3": 0,
            "penalties": 4,
        },
        "awayScore": {
            "current": 1,
            "period1": 0,
            "period2": 1,
            "period3": 0,
            "penalties": 3,
        },
    }

    update_match_score_from_sofascore(match, event_data)

    assert match.home_score == 2
    assert match.away_score == 1
    assert match.home_score_first_half == 1
    assert match.away_score_second_half == 1
    assert match.home_score_penalties == 4
    assert match.away_score_penalties == 3


@pytest.mark.django_db
def test_update_match_score_missing_scores_defaults_to_zero(
    competition_season, home_team, away_team
):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime="2025-09-01T15:00:00Z",
        status=Match.Status.TIMED,
    )

    update_match_score_from_sofascore(match, {})

    assert match.home_score == 0
    assert match.away_score == 0


@pytest.mark.django_db
def test_update_match_score_without_extra_time(
    competition_season, home_team, away_team
):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime="2025-09-01T15:00:00Z",
        status=Match.Status.FINISHED,
        home_score_extra_time=5,
    )

    event_data = {
        "homeScore": {"current": 1, "period1": 1, "period2": 0},
        "awayScore": {"current": 0, "period1": 0, "period2": 0},
    }
    update_match_score_from_sofascore(match, event_data)

    assert match.home_score == 1
    assert match.home_score_extra_time == 5
