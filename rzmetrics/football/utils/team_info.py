from django.shortcuts import get_object_or_404
from football.models import Team, Competition, CompetitionSeason, Standing


def get_team_info(team: Team, league_slug, season_name):
    league = get_object_or_404(Competition, slug=league_slug)

    competition_season = (
        CompetitionSeason.objects
        .select_related('competition', 'season')
        .filter(
            competition=league,
            season__name=season_name,
        )
        .distinct()
        .first()
    )

    seasons = (
        CompetitionSeason.objects
        .select_related('season')
        .filter(
            competition=league,
            standings__team=team,
            standings__table_type=Standing.TableType.TOTAL,
        )
        .distinct()
        .order_by('-season__name')
    )

    return league, competition_season, seasons