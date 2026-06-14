from decimal import Decimal

import pytest

from integrations.mappers.sofascore_mapper import (
    map_lineup_player,
    map_player_match_statistics,
    to_decimal,
    to_int,
    to_nullable_int,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, 0),
        (5, 5),
        ("10", 10),
        ("bad", 0),
        (3.7, 3),
    ],
)
def test_to_int(value, expected):
    assert to_int(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        (7, 7),
        ("12", 12),
        ("x", None),
    ],
)
def test_to_nullable_int(value, expected):
    assert to_nullable_int(value) == expected


@pytest.mark.parametrize(
    "value,is_none",
    [
        (None, True),
        ("7.5", False),
        ("bad", True),
        (3, False),
    ],
)
def test_to_decimal(value, is_none):
    result = to_decimal(value)
    if is_none:
        assert result is None
    else:
        assert isinstance(result, Decimal)


def test_map_lineup_player_starter():
    data = {
        "player": {"id": 100},
        "substitute": False,
        "captain": True,
        "position": "M",
        "shirtNumber": 10,
        "statistics": {
            "minutesPlayed": 90,
            "goals": 1,
            "goalAssist": 2,
            "totalShots": 3,
            "onTargetScoringAttempt": 2,
            "rating": 8.5,
        },
    }
    result = map_lineup_player(data)
    assert result["external_player_id"] == 100
    assert result["is_starting"] is True
    assert result["is_captain"] is True
    assert result["shirt_number"] == 10
    assert result["goals"] == 1
    assert result["assists"] == 2
    assert result["rating"] == Decimal("8.5")


def test_map_lineup_player_substitute():
    data = {
        "player": {"id": 200},
        "substitute": True,
        "jerseyNumber": 22,
        "statistics": {},
    }
    result = map_lineup_player(data)
    assert result["is_starting"] is False
    assert result["shirt_number"] == 22
    assert result["minutes_played"] == 0


def test_map_lineup_player_empty_stats():
    data = {"player": {"id": 1}, "statistics": None}
    result = map_lineup_player(data)
    assert result["goals"] == 0
    assert result["shots"] == 0


def test_map_player_match_statistics():
    data = {
        "statistics": {
            "minutesPlayed": 45,
            "goals": 2,
            "goalAssist": 1,
            "yellowCards": 1,
            "redCards": 0,
            "rating": 7.8,
        }
    }
    result = map_player_match_statistics(data)
    assert result["minutes_played"] == 45
    assert result["goals"] == 2
    assert result["yellow_cards"] == 1
    assert result["rating"] == 7.8


def test_map_player_match_statistics_empty():
    result = map_player_match_statistics({})
    assert result["minutes_played"] == 0
    assert result["goals"] == 0
