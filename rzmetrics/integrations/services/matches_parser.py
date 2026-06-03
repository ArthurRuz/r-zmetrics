import os
import dotenv

from django.db import close_old_connections, transaction
from django.utils.dateparse import parse_datetime
from football.models import Competition, Team, CompetitionSeason, Season, Match, MatchTeamStatistic, \
    MatchPlayerStatistic, MatchEvent
from integrations.clients.sofascore_client import SofaScoreClient
from integrations.mappers.sofascore_mapper import map_lineup_player
from integrations.models import MatchExternalMapping, TeamExternalMapping, PlayerExternalMapping
from integrations.clients.football_data_client import FootballDataClient
from integrations.mappers.football_data_mapper import map_match
from integrations.services.utils.db_helpers import add_player
from integrations.services.sofascore_worker import run_in_playwright_thread
from integrations.services.utils.match_incident_helpers import map_incident_event_type, split_incident_minute, \
    resolve_incident_players, build_incident_description

dotenv.load_dotenv()


FOOTBALL_DATA_SOURCE_ID = 1
SOFASCORE_SOURCE_ID = 4

def parse_matches(competition_code, season_name='2025-2026', season_start_year=2025):
    client = FootballDataClient(api_token=os.getenv("FOOTBALL_DATA_TOKEN"))

    competition = Competition.objects.get(competition_code=competition_code)
    season = Season.objects.get(name=season_name)

    competition_season = CompetitionSeason.objects.get(
        competition=competition,
        season=season,
    )

    data = client.get_matches_by_competition(
        competition_code,
        season_start_year,
    )

    matches = data.get("matches", [])

    with transaction.atomic():
        for match in matches:
            mapped_match = map_match(match)

            home_team = (
                TeamExternalMapping.objects
                .get(
                    external_id=mapped_match.get("home_team").get("external_id"),
                    source_id=FOOTBALL_DATA_SOURCE_ID,
                )
                .team
            )

            away_team = (
                TeamExternalMapping.objects
                .get(
                    external_id=mapped_match.get("away_team").get("external_id"),
                    source_id=FOOTBALL_DATA_SOURCE_ID,
                )
                .team
            )

            score = mapped_match.get('score', {})

            home_score = score.get('full_time_home') if score.get('full_time_home') is not None else 0
            ht_home_score = score.get('half_time_home') if score.get('half_time_home') is not None else 0

            away_score = score.get('full_time_away') if score.get('full_time_away') is not None else 0
            ht_away_score = score.get('half_time_away') if score.get('half_time_away') is not None else 0

            winner = (
                Match.Winner[score.get('winner')]
                if score.get('winner')
                else None
            )

            db_match, created = Match.objects.update_or_create(
                competition_season=competition_season,
                home_team=home_team,
                away_team=away_team,
                defaults={
                    'matchday': mapped_match.get("matchday"),
                    'competition_stage_id': 1,
                    'match_datetime': parse_datetime(mapped_match.get("utc_date")),
                    'home_score': home_score,
                    'away_score': away_score,
                    'home_score_first_half': ht_home_score,
                    'away_score_first_half': ht_away_score,
                    'home_score_second_half': home_score-ht_home_score,
                    'away_score_second_half': away_score-ht_away_score,
                    'referee_name': mapped_match.get("referee_name"),
                    'status': Match.Status[mapped_match["status"]],
                    'duration': score.get("duration"),
                    'winner': winner,
                }
            )

            MatchExternalMapping.objects.get_or_create(
                external_id=mapped_match["external_id"],
                source_id=FOOTBALL_DATA_SOURCE_ID,
                match=db_match,
            )


def get_stats(match_id: int, match: Match, client):
    stats = client.get_match_stats(match_id)

    home_team_stats = MatchTeamStatistic.objects.filter(match=match, team=match.home_team).first()
    away_team_stats = MatchTeamStatistic.objects.filter(match=match, team=match.away_team).first()

    if not home_team_stats: home_team_stats = MatchTeamStatistic(match=match, team=match.home_team)
    if not away_team_stats: away_team_stats = MatchTeamStatistic(match=match, team=match.away_team)

    match_overview_stats = stats.all.match_overview
    shot_stats = stats.all.shots
    pass_stats = stats.all.passes
    attack_stats = stats.all.attack

    home_team_stats.possession_percent = match_overview_stats.ball_possession.home_value
    away_team_stats.possession_percent = match_overview_stats.ball_possession.away_value

    home_team_stats.xg = match_overview_stats.expected_goals.home_value
    away_team_stats.xg = match_overview_stats.expected_goals.away_value

    home_team_stats.shots_total = match_overview_stats.total_shots_on_goal.home_value
    away_team_stats.shots_total = match_overview_stats.total_shots_on_goal.away_value

    home_team_stats.shots_on_target = shot_stats.shots_on_goal.home_value
    away_team_stats.shots_on_target = shot_stats.shots_on_goal.away_value

    home_team_stats.passes_total = match_overview_stats.passes.home_value
    away_team_stats.passes_total = match_overview_stats.passes.away_value

    home_team_stats.passes_accurate = pass_stats.accurate_passes.home_value
    away_team_stats.passes_accurate = pass_stats.accurate_passes.away_value

    home_team_stats.corners = match_overview_stats.corner_kicks.home_value
    away_team_stats.corners = match_overview_stats.corner_kicks.away_value

    home_team_stats.offsides = attack_stats.offsides.home_value
    away_team_stats.offsides = attack_stats.offsides.away_value

    home_team_stats.fouls = match_overview_stats.fouls.home_value
    away_team_stats.fouls = match_overview_stats.fouls.away_value

    home_team_stats.yellow_cards = match_overview_stats.yellow_cards.home_value if hasattr(
        match_overview_stats, "yellow_cards") else 0
    away_team_stats.yellow_cards = match_overview_stats.yellow_cards.away_value if hasattr(
        match_overview_stats, "yellow_cards") else 0

    home_team_stats.red_cards = 0
    away_team_stats.red_cards = 0

    home_team_stats.save()
    away_team_stats.save()

    return home_team_stats, away_team_stats


def get_lineups(
        match_id: int,
        match: Match,
        client,
        home_team_stats: MatchTeamStatistic,
        away_team_stats: MatchTeamStatistic
):
    lineup_service = SofaScoreClient(client)
    lineups_data = lineup_service.get_event_lineups(match_id)

    home_team_stats.formation = lineups_data.get("home", {}).get("formation")
    away_team_stats.formation = lineups_data.get("away", {}).get("formation")

    home_team_stats.save(update_fields=["formation"])
    away_team_stats.save(update_fields=["formation"])

    home_players = lineups_data.get("home", {}).get("players", [])
    away_players = lineups_data.get("away", {}).get("players", [])

    for player_lineup in home_players:
        make_player_stats_from_lineup(
            player_lineup=player_lineup,
            team=match.home_team,
            client=client,
            match=match,
        )

    for player_lineup in away_players:
        make_player_stats_from_lineup(
            player_lineup=player_lineup,
            team=match.away_team,
            client=client,
            match=match,
        )


def make_player_stats_from_lineup(player_lineup: dict, team: Team, client, match: Match):
    mapped_stats = map_lineup_player(player_lineup)

    external_player_id = mapped_stats["external_player_id"]
    if not external_player_id:
        return

    player_external = PlayerExternalMapping.objects.filter(
        external_id=external_player_id,
        source_id=SOFASCORE_SOURCE_ID
    ).first()

    if not player_external:
        player_external = add_player(client.get_player(external_player_id), team)

    player_stats = MatchPlayerStatistic.objects.get_or_create(
        match=match,
        team=team,
        player=player_external.player
    )[0]

    player_stats.is_starting = mapped_stats["is_starting"]
    player_stats.is_captain = mapped_stats["is_captain"]
    player_stats.formation_position = mapped_stats["formation_position"]
    player_stats.shirt_number = mapped_stats["shirt_number"]

    player_stats.minutes_played = mapped_stats["minutes_played"]
    player_stats.goals = mapped_stats["goals"]
    player_stats.assists = mapped_stats["assists"]
    player_stats.shots = mapped_stats["shots"]
    player_stats.shots_on_target = mapped_stats["shots_on_target"]
    player_stats.passes = mapped_stats["passes"]
    player_stats.accurate_passes = mapped_stats["accurate_passes"]
    player_stats.key_passes = mapped_stats["key_passes"]
    player_stats.tackles = mapped_stats["tackles"]
    player_stats.interceptions = mapped_stats["interceptions"]
    player_stats.saves = mapped_stats["saves"]
    player_stats.dribble_attempts = mapped_stats["dribble_attempts"]
    player_stats.succ_dribble = mapped_stats["succ_dribble"]
    player_stats.fouls = mapped_stats["fouls"]
    player_stats.yellow_cards = 0
    player_stats.red_cards = 0
    player_stats.rating = mapped_stats["rating"]

    player_stats.save()


def get_incidents(match_id: int, match: Match, client):
    incidents = client.get_match_incidents(match_id)

    home_team = match.home_team
    away_team = match.away_team

    for incident in incidents:
        event_type = map_incident_event_type(incident)
        if not event_type:
            continue

        team = home_team if getattr(incident, "is_home", False) else away_team

        minute, extra_minute = split_incident_minute(incident)

        player_obj, related_player_obj = resolve_incident_players(
            incident=incident,
            event_type=event_type,
        )

        description = build_incident_description(
            incident=incident,
            event_type=event_type,
        )

        MatchEvent.objects.get_or_create(
            match=match,
            team=team,
            minute=minute,
            extra_minute=extra_minute,
            event_type=event_type,
            description=description,
            defaults={
                "player": player_obj,
                "related_player": related_player_obj,
            }
        )

def update_red_cards_from_events(match, home_team_stats, away_team_stats):
    home_red_cards = MatchEvent.objects.filter(
        match=match,
        team=match.home_team,
        event_type__in=[
            'RED_CARD',
            'SECOND_YELLOW_CARD',
        ],
    ).count()

    away_red_cards = MatchEvent.objects.filter(
        match=match,
        team=match.away_team,
        event_type__in=[
            'RED_CARD',
            'SECOND_YELLOW_CARD',
        ],
    ).count()

    home_team_stats.red_cards = home_red_cards
    away_team_stats.red_cards = away_red_cards

    home_team_stats.save(update_fields=["red_cards"])
    away_team_stats.save(update_fields=["red_cards"])


def update_player_cards_from_events(match: Match):
    MatchPlayerStatistic.objects.filter(match=match).update(
        yellow_cards=0,
        red_cards=0,
    )

    card_events = MatchEvent.objects.filter(
        match=match,
        event_type__in=[
            'YELLOW_CARD',
            'RED_CARD',
            'SECOND_YELLOW_CARD',
        ],
        player__isnull=False,
    ).select_related("player")

    for event in card_events:
        player_stats = MatchPlayerStatistic.objects.filter(
            match=match,
            player=event.player,
        ).first()

        if not player_stats:
            continue

        if event.event_type == MatchEvent.EventType.YELLOW_CARD:
            player_stats.yellow_cards += 1

        elif event.event_type == MatchEvent.EventType.RED_CARD:
            player_stats.red_cards += 1

        elif event.event_type == MatchEvent.EventType.SECOND_YELLOW_CARD:
            player_stats.yellow_cards += 1
            player_stats.red_cards += 1

        player_stats.save(update_fields=["yellow_cards", "red_cards"])


def cleanup_match(match):
    MatchEvent.objects.filter(match=match).delete()
    MatchPlayerStatistic.objects.filter(match=match).delete()
    MatchTeamStatistic.objects.filter(match=match).delete()
    MatchExternalMapping.objects.filter(match=match, source_id=SOFASCORE_SOURCE_ID).delete()


def _update_single_match_details_with_client(client, match_id: int, cleanup_events: bool):
    close_old_connections()

    try:
        match = Match.objects.get(pk=match_id)

        match_mapping = MatchExternalMapping.objects.filter(
            match=match,
            source_id=SOFASCORE_SOURCE_ID,
        ).first()

        if not match_mapping:
            raise ValueError(
                f'Для матча {match.pk} нет SofaScore mapping'
            )

        sofascore_match_id = match_mapping.external_id

        if cleanup_events:
            MatchEvent.objects.filter(match=match).delete()

        home_stats, away_stats = get_stats(
            match_id=sofascore_match_id,
            match=match,
            client=client,
        )

        get_lineups(
            match_id=sofascore_match_id,
            match=match,
            client=client,
            home_team_stats=home_stats,
            away_team_stats=away_stats,
        )

        get_incidents(
            match_id=sofascore_match_id,
            match=match,
            client=client,
        )

        update_player_cards_from_events(match)
        update_red_cards_from_events(match, home_stats, away_stats)

        return match_id
    finally:
        close_old_connections()


def update_single_match_details(match: Match, cleanup_events=True):
    run_in_playwright_thread(
        _update_single_match_details_with_client,
        match.pk,
        cleanup_events,
    )
    match.refresh_from_db()
    return match