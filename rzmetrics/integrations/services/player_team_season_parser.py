from django.db.models import Sum, Count, Q

from football.models import (
    CompetitionSeason,
    Match,
    MatchEvent,
    MatchPlayerStatistic,
    PlayerTeamSeason,
)


def get_main_shirt_number(
    player_id: int,
    team_id: int,
    competition_season_id: int,
):
    row = (
        MatchPlayerStatistic.objects
        .filter(
            player_id=player_id,
            team_id=team_id,
            match__competition_season_id=competition_season_id,
            shirt_number__isnull=False,
        )
        .values("shirt_number")
        .annotate(cnt=Count("id"))
        .order_by("-cnt", "shirt_number")
        .first()
    )

    return row["shirt_number"] if row else None


def aggregate_base_player_stats(
    player_id: int,
    team_id: int,
    competition_season_id: int,
) -> dict:
    qs = MatchPlayerStatistic.objects.filter(
        player_id=player_id,
        team_id=team_id,
        match__competition_season_id=competition_season_id,
    )

    return qs.aggregate(
        matches=Count("id", filter=Q(minutes_played__gt=0)),
        started=Count("id", filter=Q(is_starting=True)),
        minutes=Sum("minutes_played"),
        goals=Sum("goals"),
        assists=Sum("assists"),
        yellow_cards=Sum("yellow_cards"),
        red_cards=Sum("red_cards"),
        saves=Sum("saves"),
    )


def aggregate_penalty_stats(
    player_id: int,
    team_id: int,
    competition_season_id: int,
) -> dict:
    events = MatchEvent.objects.filter(
        match__competition_season_id=competition_season_id,
        team_id=team_id,
        player_id=player_id,
    )

    penalty_goals = events.filter(
        event_type=MatchEvent.EventType.SCORED_PENALTY,
    ).count()

    missed_penalties = events.filter(
        event_type=MatchEvent.EventType.MISSED_PENALTY,
    ).count()

    return {
        "penalty_goals": penalty_goals,
        "penalty_attempts": penalty_goals + missed_penalties,
    }


def aggregate_goalkeeper_stats(
    player_id: int,
    team_id: int,
    competition_season_id: int,
) -> dict:
    empty_gk_stats = {
        "saves": None,
        "clean_sheets": None,
        "goals_allowed": None,
        "shots_on_target_allowed": None,
        "penalty_shots": None,
        "penalty_allowed": None,
        "penalty_saved": None,
        "penalty_missed": None,
    }

    first_stat = (
        MatchPlayerStatistic.objects
        .select_related("player")
        .filter(
            player_id=player_id,
            team_id=team_id,
            match__competition_season_id=competition_season_id,
        )
        .first()
    )

    if not first_stat or first_stat.player.main_position != "GK":
        return empty_gk_stats

    player_match_stats = (
        MatchPlayerStatistic.objects
        .select_related("match")
        .filter(
            player_id=player_id,
            team_id=team_id,
            match__competition_season_id=competition_season_id,
            minutes_played__gt=0,
        )
    )

    saves = player_match_stats.aggregate(total=Sum("saves"))["total"] or 0

    clean_sheets = 0
    goals_allowed = 0

    for stat in player_match_stats:
        match = stat.match

        if match.home_team_id == team_id:
            conceded = match.away_score
        elif match.away_team_id == team_id:
            conceded = match.home_score
        else:
            continue

        if conceded is None:
            continue

        goals_allowed += conceded

        if conceded == 0:
            clean_sheets += 1

    return {
        "saves": saves,
        "clean_sheets": clean_sheets,
        "goals_allowed": goals_allowed,
        "shots_on_target_allowed": None,
        "penalty_shots": None,
        "penalty_allowed": None,
        "penalty_saved": None,
        "penalty_missed": None,
    }


def build_player_team_season_rows(competition_season: CompetitionSeason):
    return (
        MatchPlayerStatistic.objects
        .filter(match__competition_season=competition_season)
        .values("player_id", "team_id")
        .distinct()
    )


def fill_player_team_season(competition_season: CompetitionSeason) -> int:
    updated_count = 0

    rows = build_player_team_season_rows(competition_season)

    for row in rows:
        player_id = row["player_id"]
        team_id = row["team_id"]

        base = aggregate_base_player_stats(
            player_id=player_id,
            team_id=team_id,
            competition_season_id=competition_season.pk,
        )

        penalties = aggregate_penalty_stats(
            player_id=player_id,
            team_id=team_id,
            competition_season_id=competition_season.pk,
        )

        goalkeeper = aggregate_goalkeeper_stats(
            player_id=player_id,
            team_id=team_id,
            competition_season_id=competition_season.pk,
        )

        shirt_number = resolve_shirt_number(
            player_id=player_id,
            team_id=team_id,
            competition_season=competition_season,
        )

        PlayerTeamSeason.objects.update_or_create(
            player_id=player_id,
            team_id=team_id,
            competition_season=competition_season,
            defaults={
                "shirt_number": shirt_number,

                "matches": base["matches"] or 0,
                "started": base["started"] or 0,
                "minutes": base["minutes"] or 0,
                "goals": base["goals"] or 0,
                "assists": base["assists"] or 0,
                "yellow_cards": base["yellow_cards"] or 0,
                "red_cards": base["red_cards"] or 0,

                "penalty_goals": penalties["penalty_goals"],
                "penalty_attempts": penalties["penalty_attempts"],

                "saves": goalkeeper["saves"],
                "clean_sheets": goalkeeper["clean_sheets"],
                "goals_allowed": goalkeeper["goals_allowed"],
                "shots_on_target_allowed": goalkeeper["shots_on_target_allowed"],
                "penalty_shots": goalkeeper["penalty_shots"],
                "penalty_allowed": goalkeeper["penalty_allowed"],
                "penalty_saved": goalkeeper["penalty_saved"],
                "penalty_missed": goalkeeper["penalty_missed"],
            },
        )

        updated_count += 1

    return updated_count


def resolve_shirt_number(player_id: int, team_id: int, competition_season: CompetitionSeason):
    shirt_number_from_matches = get_main_shirt_number(
        player_id=player_id,
        team_id=team_id,
        competition_season_id=competition_season.pk,
    )

    if shirt_number_from_matches is not None:
        return shirt_number_from_matches

    existing_player_team_season = PlayerTeamSeason.objects.filter(
        player_id=player_id,
        team_id=team_id,
        competition_season=competition_season,
    ).first()

    if existing_player_team_season:
        return existing_player_team_season.shirt_number

    return None