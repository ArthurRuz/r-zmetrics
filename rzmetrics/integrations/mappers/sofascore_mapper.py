from decimal import Decimal, InvalidOperation


def to_int(value, default=0):
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_nullable_int(value):
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_decimal(value):
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def map_lineup_player(api_player_lineup: dict) -> dict:
    player = api_player_lineup.get("player") or {}
    stats = api_player_lineup.get("statistics") or {}

    shots = to_int(stats.get("totalShots"))
    shots_on_target = to_int(stats.get("onTargetScoringAttempt"))

    return {
        "external_player_id": player.get("id"),

        "is_starting": not bool(api_player_lineup.get("substitute", False)),
        "is_captain": bool(api_player_lineup.get("captain", False)),
        "formation_position": api_player_lineup.get("position"),
        "shirt_number": (
            to_nullable_int(api_player_lineup.get("shirtNumber"))
            or to_nullable_int(api_player_lineup.get("jerseyNumber"))
        ),

        "minutes_played": to_int(stats.get("minutesPlayed")),
        "goals": to_int(stats.get("goals")),
        "assists": to_int(stats.get("goalAssist")),
        "shots": shots,
        "shots_on_target": shots_on_target,
        "passes": to_int(stats.get("totalPass")),
        "accurate_passes": to_int(stats.get("accuratePass")),
        "key_passes": to_int(stats.get("keyPass")),
        "tackles": to_int(stats.get("totalTackle")),
        "interceptions": to_int(stats.get("interceptionWon")),
        "saves": to_int(stats.get("saves")),
        "dribble_attempts": to_int(stats.get("totalContest")),
        "succ_dribble": to_int(stats.get("wonContest")),
        "fouls": to_int(stats.get("fouls")),
        "rating": to_decimal(stats.get("rating")),
    }




def map_player_match_statistics(api_data: dict) -> dict:
    stats = api_data.get("statistics", {}) or {}

    return {
        "minutes_played": stats.get("minutesPlayed", 0),
        "goals": stats.get("goals", 0),
        "assists": stats.get("goalAssist", 0),
        "shots": stats.get("totalShots", 0),
        "shots_on_target": stats.get("onTargetScoringAttempt", 0),
        "passes": stats.get("totalPass", 0),
        "accurate_passes": stats.get("accuratePass", 0),
        "key_passes": stats.get("keyPass", 0),
        "tackles": stats.get("totalTackle", 0),
        "interceptions": stats.get("interceptionWon", 0),
        "saves": stats.get("saves", 0),
        "dribble_attempts": stats.get("totalContest", 0),
        "succ_dribble": stats.get("wonContest", 0),
        "fouls": stats.get("fouls", 0),
        "yellow_cards": stats.get("yellowCards", 0),
        "red_cards": stats.get("redCards", 0),
        "rating": stats.get("rating"),
    }