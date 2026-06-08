from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegram.services import run_telegram_bot_polling


class Command(BaseCommand):
    help = "Запускает Telegram support bot через long polling."

    def handle(self, *args, **options):
        token = settings.TELEGRAM_MAIN_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_MAIN_BOT_TOKEN is not configured.")

        self.stdout.write(self.style.SUCCESS("Telegram support bot polling started."))
        run_telegram_bot_polling()
