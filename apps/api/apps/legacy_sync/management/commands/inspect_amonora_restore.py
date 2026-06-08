from django.core.management.base import BaseCommand, CommandError

from apps.legacy_sync.services import (
    DEFAULT_RESTORE_DB_NAME,
    inspect_amonora_device_stats,
    compare_amonora_restore_with_current,
    inspect_amonora_payment_stats,
    inspect_amonora_restore,
    inspect_amonora_subscription_stats,
    inspect_amonora_support_stats,
    inspect_amonora_user_stats,
)


class Command(BaseCommand):
    help = "Проверяет восстановленную копию Amonora в локальном PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database-name",
            default=DEFAULT_RESTORE_DB_NAME,
            help="Имя PostgreSQL базы с восстановленным дампом Amonora.",
        )
        parser.add_argument(
            "--compare-current",
            action="store_true",
            help="Показывать рядом текущие счетчики INFINDA.",
        )
        parser.add_argument(
            "--user-stats",
            action="store_true",
            help="Показать простую статистику по users в восстановленной Amonora БД.",
        )
        parser.add_argument(
            "--subscription-stats",
            action="store_true",
            help="Показать простую статистику по subscription_state в восстановленной Amonora БД.",
        )
        parser.add_argument(
            "--support-stats",
            action="store_true",
            help="Показать простую статистику по support в восстановленной Amonora БД.",
        )
        parser.add_argument(
            "--device-stats",
            action="store_true",
            help="Показать простую статистику по vpn_clients в восстановленной Amonora БД.",
        )
        parser.add_argument(
            "--payment-stats",
            action="store_true",
            help="Показать простую статистику по payment_records в восстановленной Amonora БД.",
        )

    def handle(self, *args, **options):
        database_name = str(options["database_name"]).strip()
        if not database_name:
            raise CommandError("Database name is required.")

        if options["compare_current"]:
            report = compare_amonora_restore_with_current(database_name=database_name)
            overview = report.restore
            current = report.current
        else:
            overview = inspect_amonora_restore(database_name=database_name)
            current = None

        self.stdout.write(f"database={overview.database_name}")
        self.stdout.write(f"tables={overview.table_count}")
        self.stdout.write(f"users={overview.users_count}")
        self.stdout.write(f"vpn_clients={overview.vpn_clients_count}")
        self.stdout.write(f"payment_records={overview.payment_records_count}")
        self.stdout.write(f"support_tickets={overview.support_tickets_count}")
        if current is not None:
            self.stdout.write(f"current_users={current.users_count}")
            self.stdout.write(f"current_subscriptions={current.subscriptions_count}")
            self.stdout.write(f"current_payments={current.payments_count}")
            self.stdout.write(f"current_support_conversations={current.support_conversations_count}")
            self.stdout.write(f"current_devices={current.devices_count}")

        if options["user_stats"]:
            stats = inspect_amonora_user_stats(database_name=database_name)
            self.stdout.write(f"user_total={stats.total_users}")
            self.stdout.write(f"user_blocked={stats.blocked_users}")
            self.stdout.write(f"user_synthetic={stats.synthetic_users}")
            self.stdout.write(f"user_trial={stats.trial_users}")
            self.stdout.write(f"user_active_subscription={stats.active_subscription_users}")
            self.stdout.write(f"user_referred={stats.referred_users}")
            self.stdout.write(f"user_total_balance_rub={stats.total_balance_rub}")

        if options["subscription_stats"]:
            stats = inspect_amonora_subscription_stats(database_name=database_name)
            self.stdout.write(f"subscription_users={stats.total_users_with_subscription_state}")
            self.stdout.write(f"subscription_active={stats.active_subscription_users}")
            self.stdout.write(f"subscription_trial={stats.trial_subscription_users}")
            self.stdout.write(f"subscription_expired={stats.expired_subscription_users}")
            self.stdout.write(f"subscription_inactive={stats.inactive_subscription_users}")
            self.stdout.write(f"subscription_pending_payment={stats.pending_payment_users}")

        if options["support_stats"]:
            stats = inspect_amonora_support_stats(database_name=database_name)
            self.stdout.write(f"support_total_tickets={stats.total_tickets}")
            self.stdout.write(f"support_new={stats.new_tickets}")
            self.stdout.write(f"support_in_progress={stats.in_progress_tickets}")
            self.stdout.write(f"support_closed={stats.closed_tickets}")
            self.stdout.write(f"support_assigned={stats.assigned_tickets}")
            self.stdout.write(f"support_total_messages={stats.total_messages}")
            self.stdout.write(f"support_messages_with_attachments={stats.messages_with_attachments}")

        if options["device_stats"]:
            stats = inspect_amonora_device_stats(database_name=database_name)
            self.stdout.write(f"device_total_vpn_clients={stats.total_vpn_clients}")
            self.stdout.write(f"device_unique_users={stats.unique_users_with_vpn_clients}")
            self.stdout.write(f"device_total_activations={stats.total_activations}")
            self.stdout.write(f"device_total_activation_count={stats.total_activation_count}")
            self.stdout.write(f"device_slot_entitlements={stats.device_slot_entitlements}")
            self.stdout.write(f"device_active_slot_entitlements={stats.active_device_slot_entitlements}")
            self.stdout.write(f"device_vpn_repair_events={stats.vpn_repair_events}")

        if options["payment_stats"]:
            stats = inspect_amonora_payment_stats(database_name=database_name)
            self.stdout.write(f"payment_total={stats.total_payments}")
            self.stdout.write(f"payment_confirmed={stats.confirmed_payments}")
            self.stdout.write(f"payment_pending={stats.pending_payments}")
            self.stdout.write(f"payment_awaiting_user_payment={stats.awaiting_user_payment}")
            self.stdout.write(f"payment_awaiting_admin_review={stats.awaiting_admin_review}")
            self.stdout.write(f"payment_canceled={stats.canceled_payments}")
            self.stdout.write(f"payment_rejected={stats.rejected_payments}")
            self.stdout.write(f"payment_expired={stats.expired_payments}")
            self.stdout.write(f"payment_total_amount_rub={stats.total_amount_rub}")
            self.stdout.write(f"payment_confirmed_amount_rub={stats.confirmed_amount_rub}")
