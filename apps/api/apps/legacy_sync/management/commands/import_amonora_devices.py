from django.core.management.base import BaseCommand, CommandError

from apps.legacy_sync.services import DEFAULT_RESTORE_DB_NAME, import_amonora_devices


class Command(BaseCommand):
    help = "Импортирует legacy vpn_clients в INFINDA devices."

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
            help="Импортировать только первые N устройств.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, сколько устройств будет импортировано, без записи в БД.",
        )

    def handle(self, *args, **options):
        database_name = str(options["database_name"]).strip()
        if not database_name:
            raise CommandError("Database name is required.")

        limit = options["limit"]
        if limit is not None and limit <= 0:
            raise CommandError("Limit must be a positive integer.")

        summary = import_amonora_devices(
            database_name=database_name,
            limit=limit,
            dry_run=bool(options["dry_run"]),
        )

        self.stdout.write(f"database={database_name}")
        self.stdout.write(f"source_vpn_clients={summary.source_vpn_clients}")
        self.stdout.write(f"created_devices={summary.created_devices}")
        self.stdout.write(f"active_devices={summary.active_devices}")
        self.stdout.write(f"revoked_devices={summary.revoked_devices}")
        self.stdout.write(f"skipped_missing_users={summary.skipped_missing_users}")
        self.stdout.write(f"skipped_existing_devices={summary.skipped_existing_devices}")
        self.stdout.write(f"dry_run={str(summary.dry_run).lower()}")
