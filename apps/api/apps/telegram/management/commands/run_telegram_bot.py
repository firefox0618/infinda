import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegram.bot_client import TelegramBotClient, TelegramBotClientError
from apps.telegram.bot_runtime import process_telegram_update


class Command(BaseCommand):
    help = "Запускает Telegram support bot через long polling."

    def handle(self, *args, **options):
        token = settings.TELEGRAM_MAIN_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_MAIN_BOT_TOKEN is not configured.")

        client = TelegramBotClient(
            token=token,
            api_base_url=settings.TELEGRAM_BOT_API_BASE_URL,
            request_timeout_seconds=settings.TELEGRAM_BOT_REQUEST_TIMEOUT_SECONDS,
        )
        offset = None

        self.stdout.write(self.style.SUCCESS("Telegram support bot polling started."))

        while True:
            try:
                updates = client.get_updates(
                    offset=offset,
                    timeout_seconds=settings.TELEGRAM_BOT_POLL_TIMEOUT_SECONDS,
                )
                for update in updates:
                    process_telegram_update(update=update, client=client)
                    offset = update["update_id"] + 1
            except TelegramBotClientError as exc:
                self.stderr.write(f"Telegram bot error: {exc}")
                time.sleep(settings.TELEGRAM_BOT_RETRY_DELAY_SECONDS)
