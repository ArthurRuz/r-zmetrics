import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from django.utils import timezone

from football.models import Match, LiveMatchTracking
from integrations.services.db_utils import with_scheduler_db_connection
from integrations.services.live_match_service import update_live_match_once
from integrations.services.sofascore_worker import shutdown_sofascore_worker


logger = logging.getLogger(__name__)


scheduler = BackgroundScheduler(
    timezone=str(timezone.get_current_timezone()),
)


def make_start_job_id(match_id: int) -> str:
    return f"start-live-match-{match_id}"


def make_poll_job_id(match_id: int) -> str:
    return f"poll-live-match-{match_id}"


@with_scheduler_db_connection
def start_polling_match(match_id: int):
    poll_job_id = make_poll_job_id(match_id)

    existing_job = scheduler.get_job(poll_job_id)

    if existing_job:
        logger.info("Polling для матча id=%s уже запущен", match_id)
        return

    scheduler.add_job(
        func=poll_live_match,
        trigger=IntervalTrigger(minutes=1),
        args=[match_id],
        id=poll_job_id,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info("Запущен polling для матча id=%s", match_id)

    poll_live_match(match_id)


@with_scheduler_db_connection
def poll_live_match(match_id: int):
    should_continue = update_live_match_once(match_id)

    if should_continue:
        return

    poll_job_id = make_poll_job_id(match_id)
    job = scheduler.get_job(poll_job_id)

    if job:
        job.remove()
        logger.info("Polling для матча id=%s остановлен", match_id)


def schedule_match_start(match: Match):
    start_time = timezone.localtime(match.match_datetime)
    now = timezone.localtime()

    tracking, _ = LiveMatchTracking.objects.get_or_create(match=match)

    if match.status in [
        Match.Status.IN_PLAY,
        Match.Status.PAUSED,
        Match.Status.EXTRA_TIME,
        Match.Status.PENALTY_SHOOTOUT,
    ]:
        tracking.status = LiveMatchTracking.Status.ACTIVE
        tracking.save(update_fields=["status"])

        start_polling_match(match.pk)
        return

    if start_time <= now:
        start_polling_match(match.pk)
        return

    scheduler.add_job(
        func=start_polling_match,
        trigger=DateTrigger(run_date=start_time),
        args=[match.pk],
        id=make_start_job_id(match.pk),
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    tracking.status = LiveMatchTracking.Status.PLANNED
    tracking.save(update_fields=["status"])

    logger.info(
        "Матч id=%s запланирован на live-отслеживание в %s",
        match.pk,
        start_time,
    )


def schedule_today_matches():
    today = timezone.localdate()

    matches = (
        Match.objects
        .select_related(
            "home_team",
            "away_team",
            "competition_season",
            "competition_season__competition",
            "competition_season__season",
        )
        .filter(match_datetime__date=today)
        .exclude(
            status__in=[
                Match.Status.FINISHED,
                Match.Status.SUSPENDED,
                Match.Status.POSTPONED,
                Match.Status.CANCELLED,
                Match.Status.AWARDED,
            ]
        )
    )

    for match in matches:
        schedule_match_start(match)

    logger.info("Запланированы матчи текущего дня: %s", matches.count())


def restore_live_matches():
    live_matches = (
        Match.objects
        .select_related(
            "home_team",
            "away_team",
            "competition_season",
            "competition_season__competition",
            "competition_season__season",
        )
        .filter(
            status__in=[
                Match.Status.IN_PLAY,
                Match.Status.PAUSED,
                Match.Status.EXTRA_TIME,
                Match.Status.PENALTY_SHOOTOUT,
            ]
        )
    )

    for match in live_matches:
        start_polling_match(match.pk)

    logger.info("Восстановлены live-матчи после запуска: %s", live_matches.count())


def start_live_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Live scheduler запущен")

    schedule_today_matches()
    restore_live_matches()


def stop_live_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Live scheduler остановлен")

    shutdown_sofascore_worker()