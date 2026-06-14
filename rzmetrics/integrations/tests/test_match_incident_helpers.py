from types import SimpleNamespace

import pytest

from football.models import MatchEvent
from integrations.services.utils.match_incident_helpers import (
    build_incident_description,
    get_enum_value,
    map_incident_event_type,
    split_incident_minute,
)


def _incident(**kwargs):
    defaults = {
        "type": "goal",
        "details": "",
        "reason": "",
        "text": "",
        "rescinded": False,
        "time": 45,
        "added_time": None,
        "player": SimpleNamespace(name="Player A", id=1),
        "assist_player": None,
        "player_in": None,
        "player_out": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_get_enum_value_none():
    assert get_enum_value(None) == ""


def test_get_enum_value_with_value_attr():
    obj = SimpleNamespace(value="goal")
    assert get_enum_value(obj) == "goal"


def test_get_enum_value_plain_string():
    assert get_enum_value("card") == "card"


@pytest.mark.parametrize(
    "incident_kwargs,expected",
    [
        ({"type": "goal"}, MatchEvent.EventType.GOAL),
        ({"type": "goal", "details": "owngoal"}, MatchEvent.EventType.OWN_GOAL),
        ({"type": "goal", "details": "penalty"}, MatchEvent.EventType.SCORED_PENALTY),
        ({"type": "goal", "rescinded": True}, MatchEvent.EventType.GOAL_OVERTURNED_BY_VAR),
        ({"type": "card", "details": "yellow"}, MatchEvent.EventType.YELLOW_CARD),
        ({"type": "card", "details": "red"}, MatchEvent.EventType.RED_CARD),
        ({"type": "card", "details": "yellowred"}, MatchEvent.EventType.SECOND_YELLOW_CARD),
        ({"type": "substitution"}, MatchEvent.EventType.SUBSTITUTION),
        ({"type": "inGamePenalty", "details": "scored"}, MatchEvent.EventType.SCORED_PENALTY),
        ({"type": "inGamePenalty", "details": "missed"}, MatchEvent.EventType.MISSED_PENALTY),
        ({"type": "penaltyShootout", "details": "scored"}, MatchEvent.EventType.SCORED_PENALTY),
        ({"type": "penaltyShootout", "details": "missed"}, MatchEvent.EventType.MISSED_PENALTY),
        ({"type": "period", "text": "ft"}, MatchEvent.EventType.MATCH_ENDED),
        ({"type": "period", "text": "ht"}, None),
        ({"type": "unknown"}, None),
    ],
)
def test_map_incident_event_type(incident_kwargs, expected):
    assert map_incident_event_type(_incident(**incident_kwargs)) == expected


@pytest.mark.parametrize(
    "time,added_time,expected",
    [
        (None, None, (0, None)),
        (0, 3, (0, None)),
        (-5, None, (0, None)),
        (45, None, (45, None)),
        (45, 0, (45, None)),
        (45, 999, (45, None)),
        (90, 3, (90, 3)),
    ],
)
def test_split_incident_minute(time, added_time, expected):
    incident = _incident(time=time, added_time=added_time)
    assert split_incident_minute(incident) == expected


def test_build_incident_description_goal_with_assist():
    incident = _incident(
        type="goal",
        player=SimpleNamespace(name="Haaland", id=1),
        assist_player=SimpleNamespace(name="De Bruyne", id=2),
    )
    desc = build_incident_description(incident, MatchEvent.EventType.GOAL)
    assert "Haaland" in desc
    assert "De Bruyne" in desc


def test_build_incident_description_goal_without_assist():
    incident = _incident(
        player=SimpleNamespace(name="Saka", id=1),
        assist_player=None,
    )
    desc = build_incident_description(incident, MatchEvent.EventType.GOAL)
    assert desc == "Goal: Saka"


def test_build_incident_description_substitution():
    incident = _incident(
        player_in=SimpleNamespace(name="Player In", id=1),
        player_out=SimpleNamespace(name="Player Out", id=2),
    )
    desc = build_incident_description(incident, MatchEvent.EventType.SUBSTITUTION)
    assert "Player In" in desc
    assert "Player Out" in desc


def test_build_incident_description_uses_text_when_present():
    incident = _incident(text="Custom event text")
    desc = build_incident_description(incident, MatchEvent.EventType.GOAL)
    assert desc == "Custom event text"


def test_build_incident_description_yellow_card():
    incident = _incident(
        player=SimpleNamespace(name="Rice", id=1),
        reason="Foul",
    )
    desc = build_incident_description(incident, MatchEvent.EventType.YELLOW_CARD)
    assert "Yellow card" in desc
    assert "Rice" in desc


def test_build_incident_description_match_ended():
    desc = build_incident_description(_incident(), MatchEvent.EventType.MATCH_ENDED)
    assert desc == "Match ended"


def test_build_incident_description_own_goal():
    incident = _incident(player=SimpleNamespace(name="Defender", id=1))
    desc = build_incident_description(incident, MatchEvent.EventType.OWN_GOAL)
    assert "Own goal" in desc
