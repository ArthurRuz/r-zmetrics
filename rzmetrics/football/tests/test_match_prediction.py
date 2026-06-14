import pytest
from django.utils import timezone

from football.models import Match, Standing
from football.services.match_prediction import (
    calculate_form_score,
    calculate_last_h2h_score,
    calculate_match_prediction,
    calculate_table_score,
    calculate_team_score,
    clamp,
    convert_scores_to_probabilities,
    round_probabilities_to_100,
)


@pytest.mark.parametrize(
    "value,min_val,max_val,expected",
    [
        (5, 0, 10, 5),
        (-5, 0, 10, 0),
        (15, 0, 10, 10),
        (0, 0, 100, 0),
        (50, 0, 100, 50),
    ],
)
def test_clamp(value, min_val, max_val, expected):
    assert clamp(value, min_val, max_val) == expected


def test_calculate_table_score_returns_default_for_none():
    assert calculate_table_score(None) == 50


def test_calculate_table_score_returns_default_for_zero_played(standing_factory, home_team):
    standing = standing_factory(home_team, played=0)
    assert calculate_table_score(standing) == 50


def test_calculate_table_score_leader_has_high_score(standing_factory, home_team):
    standing = standing_factory(
        home_team,
        position=1,
        played=10,
        points=30,
        goal_difference=20,
        table_type=Standing.TableType.TOTAL,
    )
    score = calculate_table_score(standing)
    assert score > 80


def test_calculate_table_score_home_type_differs_from_total(standing_factory, home_team):
    total = standing_factory(home_team, table_type=Standing.TableType.TOTAL, position=5)
    home = standing_factory(home_team, table_type=Standing.TableType.HOME, position=5)
    assert calculate_table_score(total) != calculate_table_score(home)


def test_calculate_table_score_away_type(standing_factory, away_team):
    standing = standing_factory(away_team, table_type=Standing.TableType.AWAY, position=10)
    score = calculate_table_score(standing)
    assert 0 <= score <= 100


@pytest.mark.parametrize(
    "form,expected_range",
    [
        ("", (50, 50)),
        (None, (50, 50)),
        ("WWWWW", (99, 100)),
        ("LLLLL", (0, 1)),
        ("W,D,L", (44, 45)),
        ("W W W", (99, 100)),
    ],
)
def test_calculate_form_score(standing_factory, home_team, form, expected_range):
    standing = standing_factory(home_team, form=form) if form is not None else None
    if standing is None:
        score = calculate_form_score(None)
    else:
        score = calculate_form_score(standing)
    assert expected_range[0] <= score <= expected_range[1]


def test_calculate_team_score_without_special_standing(
    standing_factory, home_team, away_team, competition_season
):
    total = standing_factory(home_team, table_type=Standing.TableType.TOTAL)
    score = calculate_team_score(
        team=home_team,
        opponent=away_team,
        total_standing=total,
        special_standing=None,
        competition_season=competition_season,
        is_home=True,
    )
    assert score >= 1


def test_calculate_team_score_away_without_special_standing(
    standing_factory, home_team, away_team, competition_season
):
    total = standing_factory(away_team, table_type=Standing.TableType.TOTAL)
    score = calculate_team_score(
        team=away_team,
        opponent=home_team,
        total_standing=total,
        special_standing=None,
        competition_season=competition_season,
        is_home=False,
    )
    assert score >= 1


def test_convert_scores_to_probabilities_sums_to_100():
    result = convert_scores_to_probabilities(70, 30)
    total = result["home_win"] + result["draw"] + result["away_win"]
    assert total == 100
    assert result["home_win"] > result["away_win"]


def test_convert_scores_to_probabilities_equal_teams():
    result = convert_scores_to_probabilities(50, 50)
    assert result["home_win"] + result["draw"] + result["away_win"] == 100


def test_convert_scores_to_probabilities_zero_total():
    result = convert_scores_to_probabilities(0, 0)
    assert result["home_win"] == 33.3
    assert result["draw"] == 33.4
    assert result["away_win"] == 33.3


def test_convert_scores_includes_raw_scores():
    result = convert_scores_to_probabilities(60.5, 40.2)
    assert result["home_score"] == 60.5
    assert result["away_score"] == 40.2


@pytest.mark.parametrize(
    "probabilities,expected_sum",
    [
        ({"home_win": 45.7, "draw": 28.3, "away_win": 26.0}, 100),
        ({"home_win": 33.3, "draw": 33.4, "away_win": 33.3}, 100),
        ({"home_win": 50.1, "draw": 25.1, "away_win": 24.8}, 100),
    ],
)
def test_round_probabilities_to_100(probabilities, expected_sum):
    rounded = round_probabilities_to_100(probabilities)
    assert sum(rounded.values()) == expected_sum


@pytest.mark.django_db
def test_calculate_last_h2h_no_matches(home_team, away_team, competition_season):
    assert calculate_last_h2h_score(home_team, away_team, competition_season) == 50


@pytest.mark.django_db
def test_calculate_last_h2h_home_win(home_team, away_team, competition_season, finished_match):
    score = calculate_last_h2h_score(home_team, away_team, competition_season)
    assert 70 <= score <= 90


@pytest.mark.django_db
def test_calculate_last_h2h_away_loss(home_team, away_team, competition_season):
    Match.objects.create(
        competition_season=competition_season,
        home_team=away_team,
        away_team=home_team,
        match_datetime=timezone.now(),
        home_score=3,
        away_score=0,
        status=Match.Status.FINISHED,
    )
    score = calculate_last_h2h_score(home_team, away_team, competition_season)
    assert 10 <= score <= 30


@pytest.mark.django_db
def test_calculate_last_h2h_draw(home_team, away_team, competition_season):
    Match.objects.create(
        competition_season=competition_season,
        home_team=home_team,
        away_team=away_team,
        match_datetime=timezone.now(),
        home_score=1,
        away_score=1,
        status=Match.Status.FINISHED,
    )
    assert calculate_last_h2h_score(home_team, away_team, competition_season) == 50


@pytest.mark.django_db
def test_calculate_match_prediction_returns_probabilities(
    standing_factory, home_team, away_team, competition_season
):
    standing_factory(home_team, table_type=Standing.TableType.TOTAL)
    standing_factory(away_team, table_type=Standing.TableType.TOTAL)
    standing_factory(home_team, table_type=Standing.TableType.HOME)
    standing_factory(away_team, table_type=Standing.TableType.AWAY)

    result = calculate_match_prediction(home_team, away_team, competition_season)

    assert result["home_win"] + result["draw"] + result["away_win"] == 100
    assert "home_score" in result
    assert "away_score" in result
