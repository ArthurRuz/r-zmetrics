from datetime import timedelta

import pytest
from django.utils import timezone

from football.models import Match


@pytest.mark.django_db
def test_match_is_live_during_match(competition_season, home_team, away_team):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime=timezone.now() - timedelta(minutes=30),
        status=Match.Status.IN_PLAY,
    )
    assert match.is_live is True


@pytest.mark.django_db
def test_match_is_not_live_before_start(competition_season, home_team, away_team):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime=timezone.now() + timedelta(hours=2),
        status=Match.Status.TIMED,
    )
    assert match.is_live is False


@pytest.mark.django_db
def test_match_is_not_live_after_window(competition_season, home_team, away_team):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime=timezone.now() - timedelta(hours=3),
        status=Match.Status.FINISHED,
    )
    assert match.is_live is False


@pytest.mark.django_db
def test_match_is_live_at_start(competition_season, home_team, away_team):
    match = Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime=timezone.now(),
        status=Match.Status.IN_PLAY,
    )
    assert match.is_live is True
