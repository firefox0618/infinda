from django.core.management.base import BaseCommand, CommandError

from apps.legacy_sync.services import (
    DEFAULT_RESTORE_DB_NAME,
    import_amonora_support,
)


class Command(BaseCommand):
    help = "Импортирует support-тикеты и сообщения из восстановленной Amonora БД."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database-name",
            default=DEFAULT_RESTORE_DB_NAME,
            help="Имя PostgreSQL базы с восстановленным дампом Amonora.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Импортировать только первые N тикетов.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, сколько support-записей будет импортировано, без записи в БД.",
        )

    def handle(self, *args, **options):
        database_name = str(options["database_name"]).strip()
        if not database_name:
            raise CommandError("Database name is required.")

        limit = options["limit"]
        if limit is not None and limit <= 0:
            raise CommandError("Limit must be a positive integer.")

        summary = import_amonora_support(
            database_name=database_name,
            limit=limit,
            dry_run=bool(options["dry_run"]),
        )

        self.stdout.write(f"database={database_name}")
        self.stdout.write(f"source_tickets={summary.source_tickets}")
        self.stdout.write(f"created_conversations={summary.created_conversations}")
        self.stdout.write(f"created_messages={summary.created_messages}")
        self.stdout.write(f"created_attachments={summary.created_attachments}")
        self.stdout.write(f"created_support_admins={summary.created_support_admins}")
        self.stdout.write(f"closed_conversations={summary.closed_conversations}")
        self.stdout.write(f"in_progress_conversations={summary.in_progress_conversations}")
        self.stdout.write(f"skipped_missing_users={summary.skipped_missing_users}")
        self.stdout.write(f"skipped_existing_conversations={summary.skipped_existing_conversations}")
        self.stdout.write(f"dry_run={str(summary.dry_run).lower()}")
