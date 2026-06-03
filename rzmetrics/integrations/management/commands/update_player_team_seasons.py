import traceback

from django.core.management.base import BaseCommand
from django.db import transaction

from football.models import CompetitionSeason
from integrations.services.player_team_season_parser import fill_player_team_season


class Command(BaseCommand):
    help = "Обновляет сезонную статистику игроков на основе статистики матчей"

    def add_arguments(self, parser):
        parser.add_argument(
            "--season",
            type=str,
            default="2025-2026",
            help="Название сезона, например 2025-2026",
        )

        parser.add_argument(
            "--competition-code",
            type=str,
            help="Код соревнования, например PL, PD, BL1, SA, FL1",
        )

    def handle(self, *args, **options):
        season_name = options["season"]
        competition_code = options["competition_code"]

        competition_seasons = (
            CompetitionSeason.objects
            .select_related("competition", "season")
            .filter(season__name=season_name)
        )

        if competition_code:
            competition_seasons = competition_seasons.filter(
                competition__competition_code=competition_code,
            )

        competition_seasons = (
            competition_seasons
            .filter(match__matchplayerstatistic__isnull=False)
            .distinct()
            .order_by("competition__name", "season__name")
        )

        if not competition_seasons.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Не найдено CompetitionSeason с матчевой статистикой"
                )
            )
            return

        total_updated = 0

        for competition_season in competition_seasons:
            try:
                with transaction.atomic():
                    count = fill_player_team_season(competition_season)

                total_updated += count

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {competition_season.competition.name} "
                        f"{competition_season.season.name}: обновлено {count}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Ошибка для CompetitionSeason.id={competition_season.id}: {e}"
                    )
                )

                traceback.print_exc()

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Всего обновлено записей PlayerTeamSeason: {total_updated}"
            )
        )