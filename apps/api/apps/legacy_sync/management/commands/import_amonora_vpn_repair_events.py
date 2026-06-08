from django.core.management.base import BaseCommand, CommandError

from apps.legacy_sync.services import (
    DEFAULT_RESTORE_DB_NAME,
    import_amonora_vpn_repair_events,
)


class Command(BaseCommand):
    help = "Импортирует legacy vpn_repair_events в INFINDA activity log."

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
            help="Импортировать только первые N записей.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, сколько записей будет импортировано, без записи в БД.",
        )

    def handle(self, *args, **options):
        database_name = str(options["database_name"]).strip()
        if not database_name:
            raise CommandError("Database name is required.")

        limit = options["limit"]
        if limit is not None and limit <= 0:
            raise CommandError("Limit must be a positive integer.")

        summary = import_amonora_vpn_repair_events(
            database_name=database_name,
            limit=limit,
            dry_run=bool(options["dry_run"]),
        )

        self.stdout.write(f"database={database_name}")
        self.stdout.write(f"source_events={summary.source_events}")
        self.stdout.write(f"created_activities={summary.created_activities}")
        self.stdout.write(f"skipped_missing_users={summary.skipped_missing_users}")
        self.stdout.write(f"skipped_existing_activities={summary.skipped_existing_activities}")
        self.stdout.write(f"dry_run={str(summary.dry_run).lower()}")
