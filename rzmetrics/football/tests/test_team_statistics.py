from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.utils import timezone

from football.models import Match, MatchTeamStatistic, Standing
from football.services.team_statistics import (
    get_defensive_stats,
    get_match_label,
    get_points_per_match,
    get_team_goals_in_match,
    get_xg_goal_chart,
    make_conclusion_based_on_xg,
    pluralize_goals,
)
from football.services.utils import safe_percent, safe_round


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, "гол"),
        (2, "гола"),
        (5, "голов"),
        (11, "голов"),
        (21, "гол"),
        (22, "гола"),
        (25, "голов"),
        (111, "голов"),
        (101, "гол"),
    ],
)
def test_pluralize_goals(value, expected):
    assert pluralize_goals(value) == expected


@pytest.mark.parametrize(
    "goals,xg,side,expected_fragment",
    [
        (10, 10.5, "забила", "согласно ожидаемым"),
        (15, 10.0, "забила", "меньше ожидаемого"),
        (5, 10.0, "забила", "больше ожидаемого"),
        (8, 7.0, "пропустила", "меньше ожидаемого"),
        (3, 3.2, "пропустила", "согласно ожидаемым"),
    ],
)
def test_make_conclusion_based_on_xg(goals, xg, side, expected_fragment):
    result = make_conclusion_based_on_xg(goals, xg, side)
    assert expected_fragment in result


def test_get_points_per_match(standing_factory, home_team):
    standing = standing_factory(home_team, points=30, played=10)
    assert get_points_per_match(standing) == 3.0


def test_get_points_per_match_zero_played(standing_factory, home_team):
    standing = standing_factory(home_team, played=0)
    assert get_points_per_match(standing) == 0


def test_get_points_per_match_none():
    assert get_points_per_match(None) == 0


@pytest.mark.parametrize(
    "goals_against_per_match,expected_reliability",
    [
        (0.5, "Надёжная оборона"),
        (1.0, "Средняя надёжность"),
        (2.0, "Есть проблемы в обороне"),
    ],
)
def test_get_defensive_stats_reliability(
    standing_factory,
    home_team,
    away_team,
    competition_season,
    finished_match,
    goals_against_per_match,
    expected_reliability,
):
    played = 10
    goals_against = int(goals_against_per_match * played)
    standing = standing_factory(
        home_team,
        played=played,
        goals_against=goals_against,
    )

    MatchTeamStatistic.objects.create(
        match=finished_match,
        team=home_team,
        possession_percent=Decimal("55.00"),
        shots_total=12,
        shots_on_target=5,
        corners=6,
        offsides=2,
        fouls=10,
        passes_total=400,
        passes_accurate=350,
        xg=Decimal("1.50"),
    )
    MatchTeamStatistic.objects.create(
        match=finished_match,
        team=away_team,
        possession_percent=Decimal("45.00"),
        shots_total=8,
        shots_on_target=3,
        corners=4,
        offsides=1,
        fouls=12,
        passes_total=300,
        passes_accurate=250,
        xg=Decimal("1.00"),
    )

    match_stats = MatchTeamStatistic.objects.filter(team=home_team)
    opponent_stats = MatchTeamStatistic.objects.filter(team=away_team)

    result = get_defensive_stats(standing, match_stats, opponent_stats, home_team)
    assert result["reliability_text"] == expected_reliability


def test_get_match_label_home(home_team, away_team, finished_match):
    label = get_match_label(finished_match, home_team)
    assert "vs" in label
    assert away_team.short_name in label or away_team.name in label


def test_get_match_label_away(home_team, away_team, finished_match):
    label = get_match_label(finished_match, away_team)
    assert "@" in label


def test_get_team_goals_in_match_home(home_team, finished_match):
    assert get_team_goals_in_match(finished_match, home_team) == 2


def test_get_team_goals_in_match_away(away_team, finished_match):
    assert get_team_goals_in_match(finished_match, away_team) == 1


@pytest.mark.django_db
def test_get_xg_goal_chart_empty(home_team):
    assert get_xg_goal_chart([], home_team) == []


@pytest.mark.django_db
def test_get_xg_goal_chart_with_data(home_team, away_team, finished_match):
    MatchTeamStatistic.objects.create(
        match=finished_match,
        team=home_team,
        possession_percent=Decimal("50.00"),
        shots_total=10,
        shots_on_target=4,
        corners=5,
        offsides=1,
        fouls=8,
        passes_total=300,
        passes_accurate=250,
        xg=Decimal("1.80"),
    )

    stats = MatchTeamStatistic.objects.filter(team=home_team)
    chart = get_xg_goal_chart(stats, home_team)

    assert len(chart) == 1
    assert chart[0]["goals"] == 2
    assert chart[0]["xg"] == 1.8
    assert 0 <= chart[0]["goals_width"] <= 100
    assert 0 <= chart[0]["xg_width"] <= 100


def test_safe_round_none():
    assert safe_round(None) == 0


def test_safe_round_value():
    assert safe_round(3.456, 2) == 3.46


def test_safe_percent_zero_total():
    assert safe_percent(5, 0) == 0


def test_safe_percent_calculation():
    assert safe_percent(1, 4) == 25
