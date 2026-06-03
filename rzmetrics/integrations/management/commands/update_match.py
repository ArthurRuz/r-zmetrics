import esd
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from football.models import Match
from integrations.services.matches_parser import update_single_match_details


os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


class Command(BaseCommand):
    help = 'Обновляет статистику, составы и события одного матча'

    def add_arguments(self, parser):
        parser.add_argument(
            'match_id',
            type=int,
            help='ID матча в локальной базе данных'
        )

        parser.add_argument(
            '--no-cleanup-events',
            action='store_true',
            help='Не удалять старые события матча перед загрузкой новых'
        )

    def handle(self, *args, **options):
        match_id = options['match_id']
        cleanup_events = not options['no_cleanup_events']

        match = (
            Match.objects
            .select_related(
                'home_team',
                'away_team',
                'competition_season',
                'competition_season__competition',
                'competition_season__season',
            )
            .filter(pk=match_id)
            .first()
        )

        if not match:
            raise CommandError(f'Матч с id={match_id} не найден')

        self.stdout.write(
            f'Обновляю матч {match.pk}: '
            f'{match.home_team.name} vs {match.away_team.name}'
        )

        client = esd.SofascoreClient()

        try:
            with transaction.atomic():
                update_single_match_details(
                    match=match,
                    client=client,
                    cleanup_events=cleanup_events,
                )

        except Exception as e:
            raise CommandError(
                f'Ошибка при обновлении матча {match.pk}: {e}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Матч {match.pk}: {match.home_team.name} vs {match.away_team.name} успешно обновлен'
            )
        )