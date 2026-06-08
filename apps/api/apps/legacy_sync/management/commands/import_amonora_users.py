from django.core.management.base import BaseCommand, CommandError

from apps.legacy_sync.services import (
    DEFAULT_RESTORE_DB_NAME,
    import_amonora_users,
)


class Command(BaseCommand):
    help = "Импортирует пользователей из восстановленной Amonora БД в INFINDA."

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
            help="Импортировать только первые N пользователей.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, сколько пользователей будет импортировано, без записи в БД.",
        )

    def handle(self, *args, **options):
        database_name = str(options["database_name"]).strip()
        if not database_name:
            raise CommandError("Database name is required.")

        limit = options["limit"]
        if limit is not None and limit <= 0:
            raise CommandError("Limit must be a positive integer.")

        summary = import_amonora_users(
            database_name=database_name,
            limit=limit,
            dry_run=bool(options["dry_run"]),
        )

        self.stdout.write(f"database={database_name}")
        self.stdout.write(f"source_users={summary.source_users}")
        self.stdout.write(f"created_users={summary.created_users}")
        self.stdout.write(f"updated_users={summary.updated_users}")
        self.stdout.write(f"created_profiles={summary.created_profiles}")
        self.stdout.write(f"created_telegram_links={summary.created_telegram_links}")
        self.stdout.write(f"dry_run={str(summary.dry_run).lower()}")
