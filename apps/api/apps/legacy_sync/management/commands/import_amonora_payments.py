from django.core.management.base import BaseCommand, CommandError

from apps.legacy_sync.services import (
    DEFAULT_RESTORE_DB_NAME,
    import_amonora_payments,
)


class Command(BaseCommand):
    help = "Импортирует платежи из восстановленной Amonora БД в INFINDA."

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
            help="Импортировать только первые N платежей.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, сколько платежей будет импортировано, без записи в БД.",
        )

    def handle(self, *args, **options):
        database_name = str(options["database_name"]).strip()
        if not database_name:
            raise CommandError("Database name is required.")

        limit = options["limit"]
        if limit is not None and limit <= 0:
            raise CommandError("Limit must be a positive integer.")

        summary = import_amonora_payments(
            database_name=database_name,
            limit=limit,
            dry_run=bool(options["dry_run"]),
        )

        self.stdout.write(f"database={database_name}")
        self.stdout.write(f"source_payments={summary.source_payments}")
        self.stdout.write(f"imported_payments={summary.imported_payments}")
        self.stdout.write(f"imported_paid_payments={summary.imported_paid_payments}")
        self.stdout.write(f"imported_pending_payments={summary.imported_pending_payments}")
        self.stdout.write(f"imported_canceled_payments={summary.imported_canceled_payments}")
        self.stdout.write(f"imported_failed_payments={summary.imported_failed_payments}")
        self.stdout.write(f"skipped_unsupported_tariffs={summary.skipped_unsupported_tariffs}")
        self.stdout.write(f"skipped_existing_payments={summary.skipped_existing_payments}")
        self.stdout.write(f"dry_run={str(summary.dry_run).lower()}")
