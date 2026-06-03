from django.core.management.base import BaseCommand
from integrations.services.standings_parser import parse_current_standings


class Command(BaseCommand):
    help = 'Парсит актуальную турнирную таблицу'

    def add_arguments(self, parser):
        parser.add_argument(
            'competition_code',
            type=str,
            help='Код соревнования, например PL, PD, BL1'
        )

        parser.add_argument(
            '--season-name',
            type=str,
            default='2025-2026',
            help='Название сезона в базе данных, например 2025-2026'
        )

        parser.add_argument(
            '--season-start-year',
            type=int,
            default=2025,
            help='Год начала сезона для football-data.org, например 2025'
        )

    def handle(self, *args, **options):
        competition_code = options['competition_code']
        season_name = options['season_name']
        season_start_year = options['season_start_year']

        self.stdout.write(
            f'Начинаю обновление таблицы: {competition_code}, {season_name}...'
        )

        parse_current_standings(
            competition_code=competition_code,
            season_name=season_name,
            season_start_year=season_start_year
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Таблица для {competition_code} за сезон {season_name} успешно обновлена'
            )
        )