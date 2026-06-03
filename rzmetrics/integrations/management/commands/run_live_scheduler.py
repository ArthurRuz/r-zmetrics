import time

from django.core.management.base import BaseCommand

from integrations.services.live_scheduler import start_live_scheduler, stop_live_scheduler


class Command(BaseCommand):
    help = "Запускает live-планировщик футбольных матчей"

    def handle(self, *args, **options):
        self.stdout.write("Запускаю live-планировщик...")

        start_live_scheduler()

        self.stdout.write(
            self.style.SUCCESS("Live-планировщик запущен")
        )

        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            self.stdout.write("Останавливаю live-планировщик...")
            stop_live_scheduler()
            self.stdout.write(
                self.style.SUCCESS("Live-планировщик остановлен")
            )