from integrations.mappers.football_data_mapper import (
    get_main_referee_name,
    map_competition,
    map_country,
    map_match,
    map_player,
    map_season,
    map_table,
    map_team,
)


def test_get_main_referee_name_empty():
    assert get_main_referee_name(None) is None
    assert get_main_referee_name([]) is None


def test_get_main_referee_name_prefers_referee_type():
    referees = [
        {"type": "FOURTH_OFFICIAL", "name": "John Assistant"},
        {"type": "REFEREE", "name": "Mike Referee"},
    ]
    assert get_main_referee_name(referees) == "Mike Referee"


def test_get_main_referee_name_fallback_to_first():
    referees = [{"type": "FOURTH_OFFICIAL", "name": "Only Official"}]
    assert get_main_referee_name(referees) == "Only Official"


def test_map_country():
    result = map_country({"id": 42, "name": "England", "countryCode": "ENG"})
    assert result["external_id"] == 42
    assert result["name"] == "England"
    assert result["iso_code"] == "ENG"


def test_map_competition():
    api_data = {
        "id": 2021,
        "name": "Premier League",
        "area": {"code": "ENG"},
        "type": "LEAGUE",
    }
    result = map_competition(api_data)
    assert result["external_id"] == 2021
    assert result["code"] == "ENG"
    assert result["type"] == "LEAGUE"


def test_map_season():
    api_data = {
        "currentMatchday": 15,
        "startDate": "2025-08-01T00:00:00Z",
        "endDate": "2026-05-31T00:00:00Z",
    }
    result = map_season(api_data)
    assert result["current_matchday"] == 15
    assert result["start_date"] is not None
    assert result["end_date"] is not None


def test_map_team():
    api_data = {
        "id": 57,
        "name": "Arsenal FC",
        "shortName": "Arsenal",
        "founded": 1886,
        "tla": "ARS",
    }
    result = map_team(api_data)
    assert result["external_id"] == 57
    assert result["short_name"] == "Arsenal"
    assert result["founded"] == 1886


def test_map_match_full():
    api_match = {
        "id": 1001,
        "utcDate": "2025-09-01T15:00:00Z",
        "status": "FINISHED",
        "matchday": 3,
        "stage": "REGULAR_SEASON",
        "competition": {"id": 2021},
        "homeTeam": {"id": 57},
        "awayTeam": {"id": 61},
        "score": {
            "winner": "HOME_TEAM",
            "duration": "REGULAR",
            "fullTime": {"home": 2, "away": 1},
            "halfTime": {"home": 1, "away": 0},
        },
        "referees": [{"type": "REFEREE", "name": "Anthony Taylor"}],
    }
    result = map_match(api_match)
    assert result["external_id"] == 1001
    assert result["score"]["full_time_home"] == 2
    assert result["score"]["half_time_away"] == 0
    assert result["referee_name"] == "Anthony Taylor"
    assert result["home_team"]["external_id"] == 57


def test_map_player():
    api_player = {
        "id": 44,
        "name": "Bukayo Saka",
        "dateOfBirth": "2001-09-05T00:00:00Z",
        "nationality": "England",
        "currentTeam": {"id": 57},
    }
    result = map_player(api_player)
    assert result["external_id"] == 44
    assert result["name"] == "Bukayo Saka"
    assert result["team_id"] == 57


def test_map_table():
    api_table = {
        "position": 1,
        "team": {"id": 57},
        "points": 30,
        "won": 10,
        "lost": 0,
        "draw": 0,
        "form": "W,W,W,W,W",
        "goalsFor": 25,
        "goalsAgainst": 5,
        "goalDifference": 20,
        "playedGames": 10,
    }
    result = map_table(api_table)
    assert result["position"] == 1
    assert result["team_id"] == 57
    assert result["played"] == 10
    assert result["goal_difference"] == 20
