import logging
import os

from django.db import transaction
from django.utils import timezone

from football.models import Match, LiveMatchTracking
from integrations.clients.sofascore_client import SofaScoreClient
from integrations.models import MatchExternalMapping
from integrations.services.db_utils import LIVE_DB_WRITE_LOCK, retry_on_db_locked
from integrations.services.matches_parser import update_single_match_details
from integrations.services.sofascore_worker import run_in_playwright_thread


os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


logger = logging.getLogger(__name__)

SOFASCORE_SOURCE_ID = 4

MATCH_LIVE_STATE_FIELDS = [
    "status",
    "home_score",
    "away_score",
    "home_score_first_half",
    "away_score_first_half",
    "home_score_second_half",
    "away_score_second_half",
    "home_score_extra_time",
    "away_score_extra_time",
    "home_score_penalties",
    "away_score_penalties",
]


LIVE_STATUSES = {
    Match.Status.IN_PLAY,
    Match.Status.PAUSED,
    Match.Status.EXTRA_TIME,
    Match.Status.PENALTY_SHOOTOUT,
}


FINAL_STATUSES = {
    Match.Status.FINISHED,
    Match.Status.SUSPENDED,
    Match.Status.POSTPONED,
    Match.Status.CANCELLED,
    Match.Status.AWARDED,
}


def map_sofascore_status(status_data: dict):
    status_type = status_data.get("type")
    description = (status_data.get("description") or "").lower()

    if status_type == "notstarted":
        return Match.Status.TIMED

    if status_type == "inprogress":
        if description in ("halftime", "half time", "break"):
            return Match.Status.PAUSED
        if description.endswith(" half") and description[0].isdigit():
            # "1st half", "2nd half"
            return Match.Status.IN_PLAY
        if "extra" in description:
            return Match.Status.EXTRA_TIME
        if "penalt" in description:
            return Match.Status.PENALTY_SHOOTOUT
        return Match.Status.IN_PLAY

    if status_type == "interrupted":
        return Match.Status.PAUSED

    if status_type == "finished":
        return Match.Status.FINISHED

    if status_type == "postponed":
        return Match.Status.POSTPONED

    if status_type in ["canceled", "cancelled"]:
        return Match.Status.CANCELLED

    return None


def update_match_score_from_sofascore(match: Match, event_data: dict):
    home_score = event_data.get("homeScore") or {}
    away_score = event_data.get("awayScore") or {}

    match.home_score = home_score.get("current") or 0
    match.away_score = away_score.get("current") or 0

    match.home_score_first_half = home_score.get("period1") or 0
    match.away_score_first_half = away_score.get("period1") or 0

    match.home_score_second_half = home_score.get("period2") or 0
    match.away_score_second_half = away_score.get("period2") or 0

    if "period3" in home_score:
        match.home_score_extra_time = home_score.get("period3") or 0

    if "period3" in away_score:
        match.away_score_extra_time = away_score.get("period3") or 0

    if "penalties" in home_score:
        match.home_score_penalties = home_score.get("penalties")

    if "penalties" in away_score:
        match.away_score_penalties = away_score.get("penalties")


def get_sofascore_event_id(match: Match):
    mapping = (
        MatchExternalMapping.objects
        .filter(
            match=match,
            source_id=SOFASCORE_SOURCE_ID,
        )
        .first()
    )

    if not mapping:
        return None

    return mapping.external_id


def _fetch_sofascore_event(client, event_id: int) -> dict:
    sofascore_client = SofaScoreClient(client)
    event_response = sofascore_client.get_event(event_id)
    return event_response.get("event", event_response)


def fetch_sofascore_event_data(match: Match) -> dict:
    sofascore_event_id = get_sofascore_event_id(match)

    if not sofascore_event_id:
        raise ValueError(f"Для матча {match.pk} нет SofaScore mapping")

    return run_in_playwright_thread(_fetch_sofascore_event, sofascore_event_id)


def apply_sofascore_event_to_match(match: Match, event_data: dict) -> Match:
    status_data = event_data.get("status") or {}
    new_status = map_sofascore_status(status_data)

    if new_status is not None:
        match.status = new_status

    update_match_score_from_sofascore(match, event_data)
    return match


def save_match_live_state(match: Match):
    match.save(update_fields=MATCH_LIVE_STATE_FIELDS)


def _save_tracking_active(tracking: LiveMatchTracking):
    tracking.status = LiveMatchTracking.Status.ACTIVE
    tracking.started_at = tracking.started_at or timezone.now()
    tracking.last_update_at = timezone.now()
    tracking.error_message = None
    tracking.save(update_fields=[
        "status",
        "started_at",
        "last_update_at",
        "error_message",
    ])


def _save_tracking_finished(tracking: LiveMatchTracking):
    tracking.status = LiveMatchTracking.Status.FINISHED
    tracking.finished_at = timezone.now()
    tracking.last_update_at = timezone.now()
    tracking.error_message = None
    tracking.save(update_fields=[
        "status",
        "finished_at",
        "last_update_at",
        "error_message",
    ])


def _save_tracking_planned(tracking: LiveMatchTracking):
    tracking.status = LiveMatchTracking.Status.PLANNED
    tracking.last_update_at = timezone.now()
    tracking.error_message = None
    tracking.save(update_fields=[
        "status",
        "last_update_at",
        "error_message",
    ])


def _save_tracking_failed(tracking: LiveMatchTracking, error_message: str):
    tracking.status = LiveMatchTracking.Status.FAILED
    tracking.error_message = error_message
    tracking.last_update_at = timezone.now()
    tracking.save(update_fields=[
        "status",
        "error_message",
        "last_update_at",
    ])


@retry_on_db_locked
def update_live_match_once(match_id: int) -> bool:
    match = (
        Match.objects
        .select_related(
            "home_team",
            "away_team",
            "competition_season",
            "competition_season__competition",
            "competition_season__season",
        )
        .filter(pk=match_id)
        .first()
    )

    if not match:
        logger.warning("Матч id=%s не найден", match_id)
        return False

    tracking, _ = LiveMatchTracking.objects.get_or_create(match=match)

    try:
        event_data = fetch_sofascore_event_data(match)
        apply_sofascore_event_to_match(match, event_data)

        needs_full_details = (
            match.status in LIVE_STATUSES
            or match.status in FINAL_STATUSES
        )

        with LIVE_DB_WRITE_LOCK:
            with transaction.atomic():
                save_match_live_state(match)

        if needs_full_details:
            update_single_match_details(
                match=match,
                cleanup_events=True,
            )

        with LIVE_DB_WRITE_LOCK:
            with transaction.atomic():
                if match.status in LIVE_STATUSES:
                    _save_tracking_active(tracking)
                    return True

                if match.status in FINAL_STATUSES:
                    _save_tracking_finished(tracking)
                    return False

                _save_tracking_planned(tracking)
                return False

    except Exception as e:
        logger.exception("Ошибка live-обновления матча id=%s", match_id)

        with LIVE_DB_WRITE_LOCK:
            _save_tracking_failed(tracking, str(e))

        return False
