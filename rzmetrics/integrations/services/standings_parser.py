import os
import dotenv

from django.db import transaction

from football.models import Competition, CompetitionSeason, Standing
from integrations.clients.football_data_client import FootballDataClient
from integrations.mappers.football_data_mapper import map_table
from integrations.models import TeamExternalMapping

dotenv.load_dotenv()

FOOTBALL_DATA_SOURCE_ID = 1


def parse_current_standings(competition_code, season_name='2025-2026', season_start_year=2025):
    client = FootballDataClient(api_token=os.getenv("FOOTBALL_DATA_TOKEN"))

    competition = Competition.objects.get(competition_code=competition_code)

    competition_season = CompetitionSeason.objects.get(season__name=season_name,
                                                       competition=competition)

    data = client.get_competition_standings(competition_code, season_start_year)

    standings = data.get('standings', [])

    for standing in standings:
        table_type = standing.get('type')
        table = standing.get('table', [])

        for row in table:
            team_standing = map_table(row)
            team = (TeamExternalMapping.objects.select_related('team')
                    .get(external_id=team_standing['team_id'], source_id=1).team)

            Standing.objects.update_or_create(
                competition_season=competition_season,
                team=team,
                table_type=Standing.TableType[table_type],
                defaults={
                    'position': team_standing.get('position'),
                    'played': team_standing.get('played'),
                    'wins': team_standing.get('won'),
                    'losses': team_standing.get('lost'),
                    'draws': team_standing.get('draw'),
                    'goals_for': team_standing.get('goals_for'),
                    'goals_against': team_standing.get('goals_against'),
                    'goal_difference': team_standing.get('goal_difference'),
                    'points': team_standing.get('points'),
                    'form': team_standing.get('form')[::-1],
                }
            )