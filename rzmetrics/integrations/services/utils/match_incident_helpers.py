from football.models import MatchEvent
from integrations.models import PlayerExternalMapping


def get_enum_value(value) -> str:
    if value is None:
        return ""

    return getattr(value, "value", str(value))


def get_player_by_external_id(external_id: int | None):
    if not external_id:
        return None

    mapping = (
        PlayerExternalMapping.objects
        .select_related("player")
        .filter(external_id=external_id, source_id=4)
        .first()
    )

    return mapping.player if mapping else None


def get_incident_player(incident):
    player = getattr(incident, "player", None)
    return get_player_by_external_id(getattr(player, "id", None))


def get_incident_assist_player(incident):
    assist_player = getattr(incident, "assist_player", None)
    return get_player_by_external_id(getattr(assist_player, "id", None))


def get_incident_player_in(incident):
    player_in = getattr(incident, "player_in", None)
    return get_player_by_external_id(getattr(player_in, "id", None))


def get_incident_player_out(incident):
    player_out = getattr(incident, "player_out", None)
    return get_player_by_external_id(getattr(player_out, "id", None))


def map_incident_event_type(incident):
    incident_type = get_enum_value(getattr(incident, "type", None))
    details = (getattr(incident, "details", "") or "").lower()
    reason = (getattr(incident, "reason", "") or "").lower()
    text = (getattr(incident, "text", "") or "").lower()

    if incident_type == "period":
        if text == "ft":
            return MatchEvent.EventType.MATCH_ENDED
        return None

    if incident_type == "goal":
        if getattr(incident, "rescinded", False):
            return MatchEvent.EventType.GOAL_OVERTURNED_BY_VAR

        if details in {"owngoal", "own goal", "own_goal"}:
            return MatchEvent.EventType.OWN_GOAL

        if details == "penalty":
            return MatchEvent.EventType.SCORED_PENALTY

        return MatchEvent.EventType.GOAL

    if incident_type == "card":
        if details == "yellow":
            return MatchEvent.EventType.YELLOW_CARD

        if details == "red":
            return MatchEvent.EventType.RED_CARD

        if details in {"yellowred", "yellow-red", "secondyellow", "second yellow"}:
            return MatchEvent.EventType.SECOND_YELLOW_CARD

        return None

    if incident_type == "substitution":
        return MatchEvent.EventType.SUBSTITUTION

    if incident_type == "inGamePenalty":
        if details == "scored":
            return MatchEvent.EventType.SCORED_PENALTY

        if details == "missed" or reason in {"goalkepersave", "goalkeepersave", "offtarget"}:
            return MatchEvent.EventType.MISSED_PENALTY

        return MatchEvent.EventType.PENALTY

    if incident_type == "penaltyShootout":
        if details == "scored":
            return MatchEvent.EventType.SCORED_PENALTY

        if details == "missed":
            return MatchEvent.EventType.MISSED_PENALTY

        return MatchEvent.EventType.PENALTY

    return None


def split_incident_minute(incident):
    minute = getattr(incident, "time", None)
    added_time = getattr(incident, "added_time", None)

    if minute is None:
        return 0, None

    if minute <= 0:
        return 0, None

    if added_time in (None, 0, 999):
        return minute, None

    return minute, added_time


def resolve_incident_players(incident, event_type):
    player_obj = None
    related_player_obj = None

    if event_type == MatchEvent.EventType.SUBSTITUTION:
        player_obj = get_incident_player_in(incident)
        related_player_obj = get_incident_player_out(incident)
        return player_obj, related_player_obj

    player_obj = get_incident_player(incident)

    if event_type in {
        MatchEvent.EventType.GOAL,
        MatchEvent.EventType.SCORED_PENALTY,
        MatchEvent.EventType.OWN_GOAL,
        MatchEvent.EventType.GOAL_OVERTURNED_BY_VAR,
    }:
        related_player_obj = get_incident_assist_player(incident)

    return player_obj, related_player_obj


def build_incident_description(incident, event_type):
    details = getattr(incident, "details", None)
    reason = getattr(incident, "reason", None)
    text = getattr(incident, "text", None)

    player = getattr(incident, "player", None)
    assist_player = getattr(incident, "assist_player", None)
    player_in = getattr(incident, "player_in", None)
    player_out = getattr(incident, "player_out", None)

    player_name = getattr(player, "name", None)
    assist_name = getattr(assist_player, "name", None)
    player_in_name = getattr(player_in, "name", None)
    player_out_name = getattr(player_out, "name", None)

    if text:
        return text

    if event_type == MatchEvent.EventType.SUBSTITUTION:
        return f"Substitution: {player_in_name} replaces {player_out_name}"

    if event_type == MatchEvent.EventType.GOAL:
        if assist_name:
            return f"Goal: {player_name}. Assist: {assist_name}"
        return f"Goal: {player_name}"

    if event_type == MatchEvent.EventType.GOAL_OVERTURNED_BY_VAR:
        return f"Goal overturned by VAR: {player_name}"

    if event_type == MatchEvent.EventType.OWN_GOAL:
        return f"Own goal: {player_name}"

    if event_type == MatchEvent.EventType.SCORED_PENALTY:
        return f"Penalty scored: {player_name}"

    if event_type == MatchEvent.EventType.MISSED_PENALTY:
        return f"Penalty missed: {player_name}. Reason: {reason or details or ''}".strip()

    if event_type == MatchEvent.EventType.YELLOW_CARD:
        return f"Yellow card: {player_name}. Reason: {reason or details or ''}".strip()

    if event_type == MatchEvent.EventType.RED_CARD:
        return f"Red card: {player_name}. Reason: {reason or details or ''}".strip()

    if event_type == MatchEvent.EventType.SECOND_YELLOW_CARD:
        return f"Second yellow card: {player_name}. Reason: {reason or details or ''}".strip()

    if event_type == MatchEvent.EventType.MATCH_ENDED:
        return "Match ended"

    return ""