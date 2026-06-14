from decimal import Decimal

import pytest

from football.models import (
    Match,
    MatchEvent,
    MatchPlayerStatistic,
    Player,
    PlayerTeamSeason,
)
from integrations.services.player_team_season_parser import (
    aggregate_base_player_stats,
    aggregate_penalty_stats,
    fill_player_team_season,
    get_main_shirt_number,
    resolve_shirt_number,
)


@pytest.fixture
def field_player(db, home_team, competition_season):
    return Player.objects.create(
        name="Test Player",
        slug="test-player",
        main_position="MF",
        current_team=home_team,
    )


@pytest.mark.django_db
def test_get_main_shirt_number(
    field_player, home_team, competition_season, finished_match
):
    MatchPlayerStatistic.objects.create(
        match=finished_match,
        team=home_team,
        player=field_player,
        shirt_number=10,
        minutes_played=90,
        is_starting=True,
    )
    number = get_main_shirt_number(
        field_player.id, home_team.id, competition_season.id
    )
    assert number == 10


@pytest.mark.django_db
def test_get_main_shirt_number_no_data(field_player, home_team, competition_season):
    assert get_main_shirt_number(
        field_player.id, home_team.id, competition_season.id
    ) is None


@pytest.mark.django_db
def test_aggregate_base_player_stats(
    field_player, home_team, competition_season, finished_match
):
    MatchPlayerStatistic.objects.create(
        match=finished_match,
        team=home_team,
        player=field_player,
        minutes_played=90,
        is_starting=True,
        goals=2,
        assists=1,
        yellow_cards=1,
    )

    stats = aggregate_base_player_stats(
        field_player.id, home_team.id, competition_season.id
    )
    assert stats["matches"] == 1
    assert stats["started"] == 1
    assert stats["goals"] == 2
    assert stats["assists"] == 1
    assert stats["yellow_cards"] == 1


@pytest.mark.django_db
def test_aggregate_penalty_stats(
    field_player, home_team, competition_season, finished_match
):
    MatchEvent.objects.create(
        match=finished_match,
        team=home_team,
        player=field_player,
        minute=55,
        event_type=MatchEvent.EventType.SCORED_PENALTY,
    )
    MatchEvent.objects.create(
        match=finished_match,
        team=home_team,
        player=field_player,
        minute=80,
        event_type=MatchEvent.EventType.MISSED_PENALTY,
    )

    stats = aggregate_penalty_stats(
        field_player.id, home_team.id, competition_season.id
    )
    assert stats["penalty_goals"] == 1
    assert stats["penalty_attempts"] == 2


@pytest.mark.django_db
def test_resolve_shirt_number_from_matches(
    field_player, home_team, competition_season, finished_match
):
    MatchPlayerStatistic.objects.create(
        match=finished_match,
        team=home_team,
        player=field_player,
        shirt_number=7,
        minutes_played=45,
    )
    number = resolve_shirt_number(field_player.id, home_team.id, competition_season)
    assert number == 7


@pytest.mark.django_db
def test_resolve_shirt_number_fallback_to_existing(
    field_player, home_team, competition_season
):
    PlayerTeamSeason.objects.create(
        player=field_player,
        team=home_team,
        competition_season=competition_season,
        shirt_number=99,
    )
    number = resolve_shirt_number(field_player.id, home_team.id, competition_season)
    assert number == 99


@pytest.mark.django_db
def test_fill_player_team_season(
    field_player, home_team, competition_season, finished_match
):
    MatchPlayerStatistic.objects.create(
        match=finished_match,
        team=home_team,
        player=field_player,
        shirt_number=11,
        minutes_played=90,
        is_starting=True,
        goals=1,
        assists=0,
    )

    count = fill_player_team_season(competition_season)
    assert count == 1

    pts = PlayerTeamSeason.objects.get(
        player=field_player,
        team=home_team,
        competition_season=competition_season,
    )
    assert pts.goals == 1
    assert pts.matches == 1
    assert pts.shirt_number == 11
