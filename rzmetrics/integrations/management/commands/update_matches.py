import esd
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from football.models import Match
from integrations.models import MatchExternalMapping
from integrations.services.matches_parser import (
    parse_matches,
    get_stats,
    get_lineups,
    get_incidents,
    update_player_cards_from_events,
    update_red_cards_from_events,
)


os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


class Command(BaseCommand):
    help = 'Обновляет матчи и статистику матчей для выбранных лиг'

    def handle(self, *args, **options):
        competitions = [
            ('PL', '2025-2026', 2025),
            ('PD', '2025-2026', 2025),
            ('BL1', '2025-2026', 2025),
            ('SA', '2025-2026', 2025),
            ('FL1', '2025-2026', 2025),
        ]

        sofascore_source_id = 4
        client = esd.SofascoreClient()

        for competition_code, season_name, season_start_year in competitions:
            self.stdout.write(
                f'Обновляю матчи: {competition_code}, {season_name}...'
            )

            parse_matches(
                competition_code=competition_code,
                season_name=season_name,
                season_start_year=season_start_year,
            )

            matches = (
                Match.objects
                .filter(
                    competition_season__competition__competition_code=competition_code,
                    competition_season__season__name=season_name,
                    status=Match.Status.FINISHED,
                )
                .filter(
                    Q(matchteamstatistic__isnull=True)
                    | Q(matchplayerstatistic__isnull=True)
                    | Q(matchevent__isnull=True)
                )
                .select_related(
                    'home_team',
                    'away_team',
                    'competition_season',
                    'competition_season__competition',
                    'competition_season__season',
                )
                .distinct()
            )

            for match in matches:
                try:
                    with transaction.atomic():
                        match_mapping = MatchExternalMapping.objects.filter(
                            match=match,
                            source_id=sofascore_source_id,
                        ).first()

                        if not match_mapping:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠️ Для матча {match.pk} {match.home_team.name} vs {match.away_team.name} '
                                    f'нет SofaScore mapping'
                                )
                            )
                            continue

                        match_id = match_mapping.external_id

                        home_stats, away_stats = get_stats(match_id, match, client)
                        get_lineups(match_id, match, client, home_stats, away_stats)
                        get_incidents(match_id, match, client)
                        update_player_cards_from_events(match)
                        update_red_cards_from_events(match, home_stats, away_stats)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {match.home_team.name} vs {match.away_team.name} добавлен'
                        )
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Ошибка при обработке матча {match.pk}: '
                            f'{match.home_team.name} vs {match.away_team.name}. {e}'
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Матчи {competition_code} успешно обновлены'
                )
            )

        self.stdout.write(
            self.style.SUCCESS('Все матчи успешно обновлены')
        )