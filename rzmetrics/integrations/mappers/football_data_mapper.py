from .mapper_utils import parse_datetime


def get_main_referee_name(referees: list[dict] | None) -> str | None:
    if not referees:
        return None

    for referee in referees:
        if referee.get("type") == "REFEREE":
            return referee.get("name")

    return referees[0].get("name")


def map_country(api_country: dict) -> dict:
    return {
        "external_id": api_country.get("id"),
        "name": api_country.get("name"),
        "iso_code":api_country.get("countryCode"),
    }


def map_competition(api_competition: dict) -> dict:
    return {
        "external_id": api_competition.get("id"),
        "name": api_competition.get("name"),
        "code": api_competition.get("area").get("code"),
        "type": api_competition.get("type"),
    }

def map_season(api_season: dict) -> dict:
    return {
        'current_matchday': api_season.get("currentMatchday"),
        'start_date': parse_datetime(api_season.get("startDate")),
        'end_date': parse_datetime(api_season.get("endDate")),
    }


def map_team(api_team: dict) -> dict:
    return {
        "external_id": api_team.get("id"),
        "name": api_team.get("name"),
        "short_name": api_team.get("shortName"),
        "founded": api_team.get("founded"),
        "tla": api_team.get("tla"),
    }

def map_match(api_match: dict) -> dict:
    full_time = api_match.get("score", {}).get("fullTime", {})
    half_time = api_match.get("score", {}).get("halfTime", {})

    return {
        "external_id": api_match.get("id"),

        "utc_date": api_match.get("utcDate"),
        "status": api_match.get("status"),
        "matchday": api_match.get("matchday"),
        "stage": api_match.get("stage"),

        "competition": {
            "external_id": api_match.get("competition", {}).get("id"),
        },

        "home_team": {
            "external_id": api_match.get("homeTeam", {}).get("id"),
        },

        "away_team": {
            "external_id": api_match.get("awayTeam", {}).get("id"),
        },

        "score": {
            "winner": api_match.get("score", {}).get("winner"),
            "duration": api_match.get("score", {}).get("duration"),

            "full_time_home": full_time.get("home"),
            "full_time_away": full_time.get("away"),

            "half_time_home": half_time.get("home"),
            "half_time_away": half_time.get("away"),
        },

        "referee_name": get_main_referee_name(api_match.get("referees")),
    }

def map_player(api_player: dict) -> dict:
    current_team = api_player.get("currentTeam", {})

    return {
        "external_id": api_player.get("id"),
        "date_of_birth": parse_datetime(api_player.get("dateOfBirth")),
        "name": api_player.get("name"),
        "nationality": api_player.get("nationality"),
        "team_id": current_team.get("id", None),
    }

def map_table(api_table: dict) -> dict:
    return {
        'position': api_table.get("position"),
        'team_id': api_table.get("team").get("id"),
        'points': api_table.get("points"),
        'won': api_table.get("won"),
        'lost': api_table.get("lost"),
        'draw': api_table.get("draw"),
        'form': api_table.get("form"),
        'goals_for': api_table.get("goalsFor"),
        'goals_against': api_table.get("goalsAgainst"),
        'goal_difference': api_table.get("goalDifference"),
        'played': api_table.get("playedGames"),
    }