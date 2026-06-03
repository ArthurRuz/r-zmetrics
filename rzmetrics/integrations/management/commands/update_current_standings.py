from django.core.management.base import BaseCommand

from integrations.services.standings_parser import parse_current_standings


class Command(BaseCommand):
    help = 'Обновляет актуальные турнирные таблицы для всех выбранных лиг'

    def handle(self, *args, **options):
        competitions = [
            ('PL', '2025-2026', 2025),
            ('PD', '2025-2026', 2025),
            ('BL1', '2025-2026', 2025),
            ('SA', '2025-2026', 2025),
            ('FL1', '2025-2026', 2025),
        ]

        for competition_code, season_name, season_start_year in competitions:
            self.stdout.write(
                f'Обновляю таблицу: {competition_code}, {season_name}...'
            )

            parse_current_standings(
                competition_code=competition_code,
                season_name=season_name,
                season_start_year=season_start_year
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Таблица {competition_code} успешно обновлена'
                )
            )

        self.stdout.write(
            self.style.SUCCESS('Все турнирные таблицы успешно обновлены')
        )