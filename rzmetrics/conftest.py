from datetime import timedelta

import pytest
from django.utils import timezone

from football.models import (
    Competition,
    CompetitionSeason,
    Country,
    Match,
    Season,
    Standing,
    Team,
)


@pytest.fixture
def country(db):
    return Country.objects.create(name="England", name_ru="Англия", alpha3="ENG")


@pytest.fixture
def season(db):
    return Season.objects.create(name="2025-2026", is_current=True)


@pytest.fixture
def competition(db, country):
    return Competition.objects.create(
        name="Premier League",
        name_ru="Премьер-лига",
        competition_code="PL",
        country=country,
        competition_type="LEAGUE",
        logo_url="logos/pl.png",
        slug="premier-league",
    )


@pytest.fixture
def competition_season(db, competition, season):
    return CompetitionSeason.objects.create(
        competition=competition,
        season=season,
        current_matchday=10,
    )


@pytest.fixture
def home_team(db, country):
    return Team.objects.create(
        name="Arsenal",
        short_name="ARS",
        name_ru="Арсенал",
        country=country,
        slug="arsenal",
        logo_url="logos/arsenal.png",
    )


@pytest.fixture
def away_team(db, country):
    return Team.objects.create(
        name="Chelsea",
        short_name="CHE",
        name_ru="Челси",
        country=country,
        slug="chelsea",
        logo_url="logos/chelsea.png",
    )


@pytest.fixture
def finished_match(db, competition_season, home_team, away_team):
    return Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime=timezone.now() - timedelta(days=3),
        home_score=2,
        away_score=1,
        status=Match.Status.FINISHED,
    )


@pytest.fixture
def standing_factory(db, competition_season):
    def _create(team, **kwargs):
        defaults = {
            "competition_season": competition_season,
            "team": team,
            "position": 1,
            "played": 10,
            "wins": 7,
            "draws": 2,
            "losses": 1,
            "goals_for": 20,
            "goals_against": 8,
            "goal_difference": 12,
            "points": 23,
            "form": "W,W,D,W,L",
            "table_type": Standing.TableType.TOTAL,
        }
        defaults.update(kwargs)
        return Standing.objects.create(**defaults)

    return _create
