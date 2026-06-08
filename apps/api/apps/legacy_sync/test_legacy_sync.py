import csv
from datetime import timedelta
from io import StringIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from django.core.management import call_command

from apps.activity.models import UserActivity
from apps.devices.models import Device
from apps.telegram.models import TelegramAccountLink
from apps.subscription.models import Subscription, SubscriptionHistoryEvent, SubscriptionPayment, SubscriptionRoute
from apps.support.models import SupportAttachment, SupportConversation, SupportMessage

from .services import (
    AmonoraRestoreComparison,
    AmonoraRestoreOverview,
    AmonoraDeviceStats,
    AmonoraPaymentStats,
    AmonoraPaymentImportSummary,
    AmonoraDeviceImportSummary,
    AmonoraDeviceSlotEntitlementImportSummary,
    AmonoraSupportImportSummary,
    AmonoraVpnRepairImportSummary,
    AmonoraSubscriptionStats,
    AmonoraSupportStats,
    AmonoraUserStats,
    AmonoraUserImportSummary,
    AmonoraSubscriptionImportSummary,
    _parse_overview,
    build_current_infinda_counts,
    compare_amonora_restore_with_current,
    inspect_amonora_device_stats,
    inspect_amonora_restore,
    inspect_amonora_payment_stats,
    inspect_amonora_subscription_stats,
    inspect_amonora_support_stats,
    inspect_amonora_user_stats,
    import_amonora_users,
    import_amonora_subscriptions,
    import_amonora_payments,
    import_amonora_devices,
    import_amonora_device_slot_entitlements,
    import_amonora_vpn_repair_events,
    import_amonora_support,
)


User = get_user_model()


class LegacySyncServiceTests(SimpleTestCase):
    def test_parse_overview_returns_counts(self):
        overview = _parse_overview(
            database_name="infinda_amonora_restore",
            output="54\n1796\n50\n394\n83\n",
        )

        self.assertEqual(
            overview,
            AmonoraRestoreOverview(
                database_name="infinda_amonora_restore",
                table_count=54,
                users_count=1796,
                vpn_clients_count=50,
                payment_records_count=394,
                support_tickets_count=83,
            ),
        )

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_inspect_amonora_restore_runs_psql(self, run_mock):
        run_mock.return_value = Mock(stdout="54\n1796\n50\n394\n83\n")

        overview = inspect_amonora_restore(database_name="legacy_restore")

        self.assertEqual(overview.database_name, "legacy_restore")
        self.assertEqual(overview.users_count, 1796)
        run_mock.assert_called_once()


class LegacySyncComparisonTests(TestCase):
    @patch("apps.legacy_sync.services.subprocess.run")
    def test_compare_report_includes_current_counts(self, run_mock):
        run_mock.return_value = Mock(stdout="54\n1796\n50\n394\n83\n")
        user = User.objects.create_user(
            username="legacy-current",
            email="legacy-current@example.com",
            password="legacy-pass-123",
        )
        Subscription.objects.create(
            user=user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate(),
            max_devices=3,
            public_token="legacy-compare-token",
            main_url="https://infinda.example/sub/current",
        )
        SubscriptionPayment.objects.create(
            user=user,
            plan_code="1m",
            plan_name="1 месяц",
            amount_rub=149,
            duration_days=30,
            max_devices=3,
            provider=SubscriptionPayment.PROVIDER_PLATEGA,
            payment_method="sbp",
            status=SubscriptionPayment.STATUS_PENDING,
        )
        SupportConversation.objects.create(user=user)
        Device.objects.create(
            user=user,
            name="Legacy laptop",
            display_name="Legacy laptop",
            icon=Device.Icon.LAPTOP,
            ip_address="127.0.0.1",
            status=Device.Status.ACTIVE,
            platform_name="Windows",
            client_name="v2rayN",
        )

        report = compare_amonora_restore_with_current(database_name="legacy_restore")

        self.assertIsInstance(report, AmonoraRestoreComparison)
        self.assertEqual(report.restore.users_count, 1796)
        self.assertEqual(report.current.users_count, 1)
        self.assertEqual(report.current.subscriptions_count, 1)
        self.assertEqual(report.current.payments_count, 1)
        self.assertEqual(report.current.support_conversations_count, 1)
        self.assertEqual(report.current.devices_count, 1)

    def test_build_current_infinda_counts_returns_numbers(self):
        counts = build_current_infinda_counts()

        self.assertEqual(counts.users_count, 0)
        self.assertEqual(counts.subscriptions_count, 0)
        self.assertEqual(counts.payments_count, 0)
        self.assertEqual(counts.support_conversations_count, 0)
        self.assertEqual(counts.devices_count, 0)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_inspect_amonora_user_stats_returns_summary(self, run_mock):
        run_mock.return_value = Mock(stdout="10\n2\n3\n4\n5\n6\n700\n")

        stats = inspect_amonora_user_stats(database_name="legacy_restore")

        self.assertEqual(
            stats,
            AmonoraUserStats(
                total_users=10,
                blocked_users=2,
                synthetic_users=3,
                trial_users=4,
                active_subscription_users=5,
                referred_users=6,
                total_balance_rub=700,
            ),
        )

    @patch("apps.legacy_sync.services.inspect_amonora_restore")
    @patch("apps.legacy_sync.services.inspect_amonora_user_stats")
    def test_management_command_prints_user_stats(self, user_stats_mock, restore_mock):
        restore_mock.return_value = AmonoraRestoreOverview(
            database_name="legacy_restore",
            table_count=54,
            users_count=1796,
            vpn_clients_count=50,
            payment_records_count=394,
            support_tickets_count=83,
        )
        user_stats_mock.return_value = AmonoraUserStats(
            total_users=10,
            blocked_users=2,
            synthetic_users=3,
            trial_users=4,
            active_subscription_users=5,
            referred_users=6,
            total_balance_rub=700,
        )

        stdout = StringIO()
        call_command(
            "inspect_amonora_restore",
            "--database-name",
            "legacy_restore",
            "--user-stats",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("user_total=10", output)
        self.assertIn("user_total_balance_rub=700", output)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_inspect_amonora_subscription_stats_returns_summary(self, run_mock):
        run_mock.return_value = Mock(stdout="100\n80\n10\n5\n3\n2\n")

        stats = inspect_amonora_subscription_stats(database_name="legacy_restore")

        self.assertEqual(
            stats,
            AmonoraSubscriptionStats(
                total_users_with_subscription_state=100,
                active_subscription_users=80,
                trial_subscription_users=10,
                expired_subscription_users=5,
                inactive_subscription_users=3,
                pending_payment_users=2,
            ),
        )

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_inspect_amonora_support_stats_returns_summary(self, run_mock):
        run_mock.return_value = Mock(stdout="83\n10\n50\n23\n14\n210\n37\n")

        stats = inspect_amonora_support_stats(database_name="legacy_restore")

        self.assertEqual(
            stats,
            AmonoraSupportStats(
                total_tickets=83,
                new_tickets=10,
                in_progress_tickets=50,
                closed_tickets=23,
                assigned_tickets=14,
                total_messages=210,
                messages_with_attachments=37,
            ),
        )

    @patch("apps.legacy_sync.services.inspect_amonora_subscription_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_support_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_user_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_restore")
    def test_management_command_prints_subscription_and_support_stats(
        self,
        restore_mock,
        user_stats_mock,
        support_stats_mock,
        subscription_stats_mock,
    ):
        restore_mock.return_value = AmonoraRestoreOverview(
            database_name="legacy_restore",
            table_count=54,
            users_count=1796,
            vpn_clients_count=50,
            payment_records_count=394,
            support_tickets_count=83,
        )
        user_stats_mock.return_value = AmonoraUserStats(
            total_users=10,
            blocked_users=2,
            synthetic_users=3,
            trial_users=4,
            active_subscription_users=5,
            referred_users=6,
            total_balance_rub=700,
        )
        subscription_stats_mock.return_value = AmonoraSubscriptionStats(
            total_users_with_subscription_state=100,
            active_subscription_users=80,
            trial_subscription_users=10,
            expired_subscription_users=5,
            inactive_subscription_users=3,
            pending_payment_users=2,
        )
        support_stats_mock.return_value = AmonoraSupportStats(
            total_tickets=83,
            new_tickets=10,
            in_progress_tickets=50,
            closed_tickets=23,
            assigned_tickets=14,
            total_messages=210,
            messages_with_attachments=37,
        )

        stdout = StringIO()
        call_command(
            "inspect_amonora_restore",
            "--database-name",
            "legacy_restore",
            "--user-stats",
            "--subscription-stats",
            "--support-stats",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("subscription_active=80", output)
        self.assertIn("support_total_tickets=83", output)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_inspect_amonora_device_stats_returns_summary(self, run_mock):
        run_mock.return_value = Mock(stdout="50\n42\n60\n120\n11\n9\n17\n")

        stats = inspect_amonora_device_stats(database_name="legacy_restore")

        self.assertEqual(
            stats,
            AmonoraDeviceStats(
                total_vpn_clients=50,
                unique_users_with_vpn_clients=42,
                total_activations=60,
                total_activation_count=120,
                device_slot_entitlements=11,
                active_device_slot_entitlements=9,
                vpn_repair_events=17,
            ),
        )

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_inspect_amonora_payment_stats_returns_summary(self, run_mock):
        run_mock.return_value = Mock(stdout="394\n200\n80\n40\n30\n20\n12\n8\n123456\n98765\n")

        stats = inspect_amonora_payment_stats(database_name="legacy_restore")

        self.assertEqual(
            stats,
            AmonoraPaymentStats(
                total_payments=394,
                confirmed_payments=200,
                pending_payments=80,
                awaiting_user_payment=40,
                awaiting_admin_review=30,
                canceled_payments=20,
                rejected_payments=12,
                expired_payments=8,
                total_amount_rub=123456,
                confirmed_amount_rub=98765,
            ),
        )

    @patch("apps.legacy_sync.services.inspect_amonora_device_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_payment_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_support_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_subscription_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_user_stats")
    @patch("apps.legacy_sync.services.inspect_amonora_restore")
    def test_management_command_prints_device_and_payment_stats(
        self,
        restore_mock,
        user_stats_mock,
        subscription_stats_mock,
        support_stats_mock,
        payment_stats_mock,
        device_stats_mock,
    ):
        restore_mock.return_value = AmonoraRestoreOverview(
            database_name="legacy_restore",
            table_count=54,
            users_count=1796,
            vpn_clients_count=50,
            payment_records_count=394,
            support_tickets_count=83,
        )
        user_stats_mock.return_value = AmonoraUserStats(
            total_users=10,
            blocked_users=2,
            synthetic_users=3,
            trial_users=4,
            active_subscription_users=5,
            referred_users=6,
            total_balance_rub=700,
        )
        subscription_stats_mock.return_value = AmonoraSubscriptionStats(
            total_users_with_subscription_state=100,
            active_subscription_users=80,
            trial_subscription_users=10,
            expired_subscription_users=5,
            inactive_subscription_users=3,
            pending_payment_users=2,
        )
        support_stats_mock.return_value = AmonoraSupportStats(
            total_tickets=83,
            new_tickets=10,
            in_progress_tickets=50,
            closed_tickets=23,
            assigned_tickets=14,
            total_messages=210,
            messages_with_attachments=37,
        )
        payment_stats_mock.return_value = AmonoraPaymentStats(
            total_payments=394,
            confirmed_payments=200,
            pending_payments=80,
            awaiting_user_payment=40,
            awaiting_admin_review=30,
            canceled_payments=20,
            rejected_payments=12,
            expired_payments=8,
            total_amount_rub=123456,
            confirmed_amount_rub=98765,
        )
        device_stats_mock.return_value = AmonoraDeviceStats(
            total_vpn_clients=50,
            unique_users_with_vpn_clients=42,
            total_activations=60,
            total_activation_count=120,
            device_slot_entitlements=11,
            active_device_slot_entitlements=9,
            vpn_repair_events=17,
        )

        stdout = StringIO()
        call_command(
            "inspect_amonora_restore",
            "--database-name",
            "legacy_restore",
            "--device-stats",
            "--payment-stats",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("device_total_vpn_clients=50", output)
        self.assertIn("payment_confirmed=200", output)


class LegacySyncImportTests(TestCase):
    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_users_creates_users_profiles_and_links(self, run_mock):
        run_mock.return_value = Mock(
            stdout=(
                "1\t5931568924\teo860\t2026-03-18 15:25:53.19416\tf\n"
                "2\t573125316\tsd_pride\t2026-03-26 08:46:25.19702\tt\n"
            ),
        )
        stale_user = User.objects.create_user(
            username="stale-user",
            email="stale-user@infinda.local",
            password="pass-123",
        )
        TelegramAccountLink.objects.create(
            user=stale_user,
            telegram_user_id=5931568924,
            telegram_username="stale-eo860",
            telegram_full_name="",
            is_active=False,
        )

        summary = import_amonora_users(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraUserImportSummary(
                source_users=2,
                created_users=2,
                updated_users=0,
                created_profiles=2,
                created_telegram_links=1,
                dry_run=False,
            ),
        )
        self.assertEqual(User.objects.count(), 3)

        first_user = User.objects.get(username="amonora-1")
        self.assertEqual(first_user.email, "amonora-1@infinda.local")
        self.assertEqual(first_user.first_name, "eo860")
        self.assertTrue(first_user.is_active)
        self.assertFalse(first_user.has_usable_password())
        self.assertTrue(
            TelegramAccountLink.objects.filter(
                user=first_user,
                telegram_user_id=5931568924,
                telegram_username="eo860",
                is_active=True,
            ).exists()
        )
        self.assertFalse(TelegramAccountLink.objects.filter(user=stale_user).exists())

        second_user = User.objects.get(username="amonora-2")
        self.assertFalse(second_user.is_active)
        self.assertTrue(
            TelegramAccountLink.objects.filter(
                user=second_user,
                telegram_user_id=573125316,
                telegram_username="sd_pride",
                is_active=False,
            ).exists()
        )

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_users_is_idempotent(self, run_mock):
        run_mock.return_value = Mock(
            stdout="1\t5931568924\teo860\t2026-03-18 15:25:53.19416\tf\n",
        )

        first_summary = import_amonora_users(database_name="legacy_restore")
        second_summary = import_amonora_users(database_name="legacy_restore")

        self.assertEqual(first_summary.created_users, 1)
        self.assertEqual(second_summary.created_users, 0)
        self.assertEqual(second_summary.updated_users, 0)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(TelegramAccountLink.objects.count(), 1)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_users_supports_dry_run(self, run_mock):
        run_mock.return_value = Mock(
            stdout="1\t5931568924\teo860\t2026-03-18 15:25:53.19416\tf\n",
        )

        summary = import_amonora_users(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraUserImportSummary(
                source_users=1,
                created_users=0,
                updated_users=0,
                created_profiles=0,
                created_telegram_links=0,
                dry_run=True,
            ),
        )
        self.assertEqual(User.objects.count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_users.import_amonora_users")
    def test_management_command_prints_import_summary(self, import_mock):
        import_mock.return_value = AmonoraUserImportSummary(
            source_users=3,
            created_users=3,
            updated_users=0,
            created_profiles=3,
            created_telegram_links=3,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_users",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("source_users=3", output)
        self.assertIn("created_users=3", output)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_subscriptions_creates_subscription_records(self, run_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        User.objects.create_user(
            username="amonora-2",
            email="amonora-2@infinda.local",
            password="pass-123",
        )
        User.objects.create_user(
            username="amonora-3",
            email="amonora-3@infinda.local",
            password="pass-123",
        )
        run_mock.return_value = Mock(
            stdout=(
                "1\t5931568924\teo860\t2026-03-18 15:25:53.19416\tf\t\t\t2026-03-18 18:05:11.742066\t2026-06-04 07:59:40.585424\tactive\tplatega_sbp\n"
                "2\t573125316\tsd_pride\t2026-03-26 08:46:25.19702\tt\t2026-04-15 20:32:04.509651\t2026-04-18 20:32:04.509651\t2026-04-18 20:53:20.682715\t2026-06-17 21:08:35.149942\tactive\tplatega_sbp\n"
                "3\t8565978814\tDuldov\t2026-03-31 19:18:55.192064\tt\t2026-03-31 19:19:04.00595\t2026-04-03 19:19:04.00595\t\t\tinactive\t\n"
            ),
        )

        summary = import_amonora_subscriptions(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraSubscriptionImportSummary(
                source_users=3,
                created_subscriptions=2,
                created_trial_subscriptions=0,
                created_active_subscriptions=2,
                created_expired_subscriptions=0,
                skipped_inactive_users=1,
                skipped_existing_subscriptions=0,
                dry_run=False,
            ),
        )
        self.assertEqual(Subscription.objects.count(), 2)
        self.assertEqual(SubscriptionRoute.objects.count(), 8)
        self.assertEqual(SubscriptionHistoryEvent.objects.count(), 2)

        first_subscription = Subscription.objects.get(user__username="amonora-1")
        self.assertEqual(first_subscription.plan_name, "3 месяца")
        self.assertEqual(first_subscription.max_devices, 4)
        self.assertEqual(first_subscription.routes.count(), 4)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_subscriptions_is_idempotent(self, run_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        run_mock.return_value = Mock(
            stdout=(
                "1\t5931568924\teo860\t2026-03-18 15:25:53.19416\tf\t\t\t2026-03-18 18:05:11.742066\t2026-06-04 07:59:40.585424\tactive\tplatega_sbp\n"
            ),
        )

        first_summary = import_amonora_subscriptions(database_name="legacy_restore")
        second_summary = import_amonora_subscriptions(database_name="legacy_restore")

        self.assertEqual(first_summary.created_subscriptions, 1)
        self.assertEqual(second_summary.created_subscriptions, 0)
        self.assertEqual(Subscription.objects.count(), 1)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_subscriptions_supports_dry_run(self, run_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        run_mock.return_value = Mock(
            stdout=(
                "1\t5931568924\teo860\t2026-03-18 15:25:53.19416\tf\t\t\t2026-03-18 18:05:11.742066\t2026-06-04 07:59:40.585424\tactive\tplatega_sbp\n"
            ),
        )

        summary = import_amonora_subscriptions(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraSubscriptionImportSummary(
                source_users=1,
                created_subscriptions=1,
                created_trial_subscriptions=0,
                created_active_subscriptions=1,
                created_expired_subscriptions=0,
                skipped_inactive_users=0,
                skipped_existing_subscriptions=0,
                dry_run=True,
            ),
        )
        self.assertEqual(Subscription.objects.count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_subscriptions.import_amonora_subscriptions")
    def test_management_command_prints_subscription_import_summary(self, import_mock):
        import_mock.return_value = AmonoraSubscriptionImportSummary(
            source_users=4,
            created_subscriptions=2,
            created_trial_subscriptions=1,
            created_active_subscriptions=1,
            created_expired_subscriptions=0,
            skipped_inactive_users=2,
            skipped_existing_subscriptions=0,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_subscriptions",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("created_subscriptions=2", output)
        self.assertIn("created_trial_subscriptions=1", output)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_payments_creates_payment_records(self, run_mock):
        User.objects.create_user(
            username="amonora-82",
            email="amonora-82@infinda.local",
            password="pass-123",
        )
        User.objects.create_user(
            username="amonora-113",
            email="amonora-113@infinda.local",
            password="pass-123",
        )
        first_row = "\t".join(
            [
                "43",
                "82",
                "manual_sbp_manual_404ad36a9ad94387",
                "1m",
                "sbp_manual",
                "confirmed",
                "149",
                "RUB",
                "30",
                "",
                "2026-03-21 06:30:44.70905",
                "2026-03-21 06:22:52.681367",
                "",
                '{"tariff_title": "1 месяц", "telegram_id": 2024312924}',
                "legacy-support:82",
                "Dexus @dextrmed",
                "2026-03-21 06:30:44.70905",
                "",
                "2026-03-21 18:22:52.671224",
                "0",
                "0",
                "0",
            ],
        )
        second_row = "\t".join(
            [
                "58",
                "113",
                "manual_sbp_manual_2c36d36afcbc4083",
                "1m",
                "sbp_manual",
                "confirmed",
                "149",
                "RUB",
                "30",
                "",
                "2026-03-23 11:45:00.201391",
                "2026-03-23 11:41:11.717603",
                "",
                '{"tariff_title": "1 месяц", "telegram_id": 6971658933}',
                "control_bot:548589949",
                "Ruslan Ix@n",
                "2026-03-23 11:45:00.201391",
                "",
                "2026-03-23 23:41:11.709616",
                "149",
                "0",
                "0",
            ],
        )
        third_row = "\t".join(
            [
                "999",
                "82",
                "balance_topup_1",
                "balance_topup",
                "manual",
                "confirmed",
                "1000",
                "RUB",
                "0",
                "",
                "2026-03-23 11:45:00.201391",
                "2026-03-23 11:41:11.717603",
                "",
                "{}",
                "",
                "",
                "",
                "",
                "",
                "0",
                "0",
                "0",
            ],
        )
        run_mock.return_value = Mock(
            stdout=f"{first_row}\n{second_row}\n{third_row}\n",
        )

        summary = import_amonora_payments(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraPaymentImportSummary(
                source_payments=3,
                imported_payments=2,
                imported_paid_payments=2,
                imported_pending_payments=0,
                imported_canceled_payments=0,
                imported_failed_payments=0,
                skipped_unsupported_tariffs=1,
                skipped_existing_payments=0,
                dry_run=False,
            ),
        )
        self.assertEqual(SubscriptionPayment.objects.count(), 2)
        first_payment = SubscriptionPayment.objects.get(external_payment_id="manual_sbp_manual_404ad36a9ad94387")
        self.assertEqual(first_payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(first_payment.plan_code, "1m")
        self.assertEqual(first_payment.amount_rub, 149)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_payments_is_idempotent(self, run_mock):
        User.objects.create_user(
            username="amonora-82",
            email="amonora-82@infinda.local",
            password="pass-123",
        )
        row = "\t".join(
            [
                "43",
                "82",
                "manual_sbp_manual_404ad36a9ad94387",
                "1m",
                "sbp_manual",
                "confirmed",
                "149",
                "RUB",
                "30",
                "",
                "2026-03-21 06:30:44.70905",
                "2026-03-21 06:22:52.681367",
                "",
                '{"tariff_title": "1 месяц", "telegram_id": 2024312924}',
                "legacy-support:82",
                "Dexus @dextrmed",
                "2026-03-21 06:30:44.70905",
                "",
                "2026-03-21 18:22:52.671224",
                "0",
                "0",
                "0",
            ],
        )
        run_mock.return_value = Mock(
            stdout=f"{row}\n",
        )

        first_summary = import_amonora_payments(database_name="legacy_restore")
        second_summary = import_amonora_payments(database_name="legacy_restore")

        self.assertEqual(first_summary.imported_payments, 1)
        self.assertEqual(second_summary.imported_payments, 0)
        self.assertEqual(SubscriptionPayment.objects.count(), 1)

    @patch("apps.legacy_sync.services.subprocess.run")
    def test_import_amonora_payments_supports_dry_run(self, run_mock):
        User.objects.create_user(
            username="amonora-82",
            email="amonora-82@infinda.local",
            password="pass-123",
        )
        row = "\t".join(
            [
                "43",
                "82",
                "manual_sbp_manual_404ad36a9ad94387",
                "1m",
                "sbp_manual",
                "confirmed",
                "149",
                "RUB",
                "30",
                "",
                "2026-03-21 06:30:44.70905",
                "2026-03-21 06:22:52.681367",
                "",
                '{"tariff_title": "1 месяц", "telegram_id": 2024312924}',
                "legacy-support:82",
                "Dexus @dextrmed",
                "2026-03-21 06:30:44.70905",
                "",
                "2026-03-21 18:22:52.671224",
                "0",
                "0",
                "0",
            ],
        )
        run_mock.return_value = Mock(
            stdout=f"{row}\n",
        )

        summary = import_amonora_payments(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraPaymentImportSummary(
                source_payments=1,
                imported_payments=1,
                imported_paid_payments=1,
                imported_pending_payments=0,
                imported_canceled_payments=0,
                imported_failed_payments=0,
                skipped_unsupported_tariffs=0,
                skipped_existing_payments=0,
                dry_run=True,
            ),
        )
        self.assertEqual(SubscriptionPayment.objects.count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_payments.import_amonora_payments")
    def test_management_command_prints_payment_import_summary(self, import_mock):
        import_mock.return_value = AmonoraPaymentImportSummary(
            source_payments=3,
            imported_payments=2,
            imported_paid_payments=2,
            imported_pending_payments=0,
            imported_canceled_payments=0,
            imported_failed_payments=0,
            skipped_unsupported_tariffs=1,
            skipped_existing_payments=0,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_payments",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("imported_payments=2", output)
        self.assertIn("skipped_unsupported_tariffs=1", output)

    @patch("apps.legacy_sync.services._fetch_amonora_vpn_clients")
    def test_import_amonora_devices_creates_devices(self, fetch_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        User.objects.create_user(
            username="amonora-2",
            email="amonora-2@infinda.local",
            password="pass-123",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 1,
                "legacy_user_id": 10,
                "username": "amonora-1",
                "protocol": "vless",
                "client_uuid": "uuid-1",
                "email": "device-1@example.com",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "xui_client_id": "xui-1",
                "client_data": {
                    "device_name": "Мурадым телефон",
                    "device_type": "android",
                    "retired": False,
                },
                "ip_address": "0.0.0.0",
            },
            {
                "legacy_id": 2,
                "legacy_user_id": 11,
                "username": "amonora-2",
                "protocol": "vless",
                "client_uuid": "uuid-2",
                "email": "device-2@example.com",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 0, 51, 20)),
                "xui_client_id": "xui-2",
                "client_data": {
                    "device_name": "Кирилл",
                    "device_type": "ios",
                    "retired": True,
                },
                "ip_address": "0.0.0.0",
            },
        ]

        summary = import_amonora_devices(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraDeviceImportSummary(
                source_vpn_clients=2,
                created_devices=2,
                active_devices=1,
                revoked_devices=1,
                skipped_missing_users=0,
                skipped_existing_devices=0,
                dry_run=False,
            ),
        )
        self.assertEqual(Device.objects.count(), 2)
        first_device = Device.objects.get(name="uuid-1")
        self.assertEqual(first_device.display_name, "Мурадым телефон")
        self.assertEqual(first_device.status, Device.Status.ACTIVE)
        second_device = Device.objects.get(name="uuid-2")
        self.assertEqual(second_device.status, Device.Status.REVOKED)
        self.assertEqual(second_device.revoked_reason, "legacy-retired")

    @patch("apps.legacy_sync.services._fetch_amonora_vpn_clients")
    def test_import_amonora_devices_is_idempotent(self, fetch_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 1,
                "legacy_user_id": 10,
                "username": "amonora-1",
                "protocol": "vless",
                "client_uuid": "uuid-1",
                "email": "device-1@example.com",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "xui_client_id": "xui-1",
                "client_data": {
                    "device_name": "Мурадым телефон",
                    "device_type": "android",
                    "retired": False,
                },
                "ip_address": "0.0.0.0",
            }
        ]

        first_summary = import_amonora_devices(database_name="legacy_restore")
        second_summary = import_amonora_devices(database_name="legacy_restore")

        self.assertEqual(first_summary.created_devices, 1)
        self.assertEqual(second_summary.created_devices, 0)
        self.assertEqual(Device.objects.count(), 1)

    @patch("apps.legacy_sync.services._fetch_amonora_vpn_clients")
    def test_import_amonora_devices_supports_dry_run(self, fetch_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 1,
                "legacy_user_id": 10,
                "username": "amonora-1",
                "protocol": "vless",
                "client_uuid": "uuid-1",
                "email": "device-1@example.com",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "xui_client_id": "xui-1",
                "client_data": {
                    "device_name": "Мурадым телефон",
                    "device_type": "android",
                    "retired": False,
                },
                "ip_address": "0.0.0.0",
            }
        ]

        summary = import_amonora_devices(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraDeviceImportSummary(
                source_vpn_clients=1,
                created_devices=1,
                active_devices=1,
                revoked_devices=0,
                skipped_missing_users=0,
                skipped_existing_devices=0,
                dry_run=True,
            ),
        )
        self.assertEqual(Device.objects.count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_devices.import_amonora_devices")
    def test_management_command_prints_device_import_summary(self, import_mock):
        import_mock.return_value = AmonoraDeviceImportSummary(
            source_vpn_clients=2,
            created_devices=2,
            active_devices=1,
            revoked_devices=1,
            skipped_missing_users=0,
            skipped_existing_devices=0,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_devices",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("created_devices=2", output)
        self.assertIn("revoked_devices=1", output)

    @patch("apps.legacy_sync.services._fetch_amonora_device_slot_entitlements")
    def test_import_amonora_device_slot_entitlements_updates_subscription_and_activity(self, fetch_mock):
        user = User.objects.create_user(
            username="amonora-59",
            email="amonora-59@infinda.local",
            password="pass-123",
        )
        Subscription.objects.create(
            user=user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="legacy-slot-token-1",
            main_url="https://infinda.example/sub/1",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 1,
                "legacy_user_id": 59,
                "payment_record_id": 175,
                "slots_count": 1,
                "unit_price_rub": 49,
                "total_amount_rub": 49,
                "starts_at": timezone.make_aware(timezone.datetime(2026, 3, 20, 8, 55, 49)),
                "expires_at": timezone.make_aware(timezone.datetime(2027, 1, 14, 8, 55, 49)),
                "status": "active",
            },
            {
                "legacy_id": 2,
                "legacy_user_id": 59,
                "payment_record_id": 152,
                "slots_count": 1,
                "unit_price_rub": 49,
                "total_amount_rub": 49,
                "starts_at": timezone.make_aware(timezone.datetime(2026, 3, 25, 19, 24, 25)),
                "expires_at": timezone.make_aware(timezone.datetime(2026, 4, 24, 19, 24, 25)),
                "status": "expired",
            },
        ]

        summary = import_amonora_device_slot_entitlements(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraDeviceSlotEntitlementImportSummary(
                source_entitlements=2,
                updated_subscriptions=1,
                created_activities=2,
                skipped_missing_users=0,
                skipped_existing_activities=0,
                dry_run=False,
            ),
        )
        subscription = Subscription.objects.get(user=user)
        self.assertEqual(subscription.max_devices, 4)
        self.assertEqual(
            UserActivity.objects.filter(user=user, action=UserActivity.Action.VPN_DEVICE_SLOT_UPDATED).count(),
            2,
        )

    @patch("apps.legacy_sync.services._fetch_amonora_device_slot_entitlements")
    def test_import_amonora_device_slot_entitlements_is_idempotent(self, fetch_mock):
        user = User.objects.create_user(
            username="amonora-59",
            email="amonora-59@infinda.local",
            password="pass-123",
        )
        Subscription.objects.create(
            user=user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="legacy-slot-token-2",
            main_url="https://infinda.example/sub/1",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 1,
                "legacy_user_id": 59,
                "payment_record_id": 175,
                "slots_count": 1,
                "unit_price_rub": 49,
                "total_amount_rub": 49,
                "starts_at": timezone.make_aware(timezone.datetime(2026, 3, 20, 8, 55, 49)),
                "expires_at": timezone.make_aware(timezone.datetime(2027, 1, 14, 8, 55, 49)),
                "status": "active",
            }
        ]

        first_summary = import_amonora_device_slot_entitlements(database_name="legacy_restore")
        second_summary = import_amonora_device_slot_entitlements(database_name="legacy_restore")

        self.assertEqual(first_summary.created_activities, 1)
        self.assertEqual(second_summary.created_activities, 0)
        self.assertEqual(UserActivity.objects.filter(user=user).count(), 1)

    @patch("apps.legacy_sync.services._fetch_amonora_device_slot_entitlements")
    def test_import_amonora_device_slot_entitlements_supports_dry_run(self, fetch_mock):
        user = User.objects.create_user(
            username="amonora-59",
            email="amonora-59@infinda.local",
            password="pass-123",
        )
        Subscription.objects.create(
            user=user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="legacy-slot-token-3",
            main_url="https://infinda.example/sub/1",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 1,
                "legacy_user_id": 59,
                "payment_record_id": 175,
                "slots_count": 1,
                "unit_price_rub": 49,
                "total_amount_rub": 49,
                "starts_at": timezone.make_aware(timezone.datetime(2026, 3, 20, 8, 55, 49)),
                "expires_at": timezone.make_aware(timezone.datetime(2027, 1, 14, 8, 55, 49)),
                "status": "active",
            }
        ]

        summary = import_amonora_device_slot_entitlements(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraDeviceSlotEntitlementImportSummary(
                source_entitlements=1,
                updated_subscriptions=0,
                created_activities=0,
                skipped_missing_users=0,
                skipped_existing_activities=0,
                dry_run=True,
            ),
        )
        self.assertEqual(UserActivity.objects.count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_device_slot_entitlements.import_amonora_device_slot_entitlements")
    def test_management_command_prints_device_slot_entitlement_summary(self, import_mock):
        import_mock.return_value = AmonoraDeviceSlotEntitlementImportSummary(
            source_entitlements=2,
            updated_subscriptions=1,
            created_activities=2,
            skipped_missing_users=0,
            skipped_existing_activities=0,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_device_slot_entitlements",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("updated_subscriptions=1", output)
        self.assertIn("created_activities=2", output)

    @patch("apps.legacy_sync.services._fetch_amonora_vpn_repair_events")
    def test_import_amonora_vpn_repair_events_creates_activity_records(self, fetch_mock):
        user = User.objects.create_user(
            username="amonora-18",
            email="amonora-18@infinda.local",
            password="pass-123",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 2,
                "legacy_user_id": 18,
                "result": "success",
                "reason": "manual_repair",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 23, 1, 40, 14)),
            },
            {
                "legacy_id": 5,
                "legacy_user_id": 18,
                "result": "failed",
                "reason": "auto_repair_failed",
                "created_at": timezone.make_aware(timezone.datetime(2026, 4, 3, 19, 44, 15)),
            },
        ]

        summary = import_amonora_vpn_repair_events(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraVpnRepairImportSummary(
                source_events=2,
                created_activities=2,
                skipped_missing_users=0,
                skipped_existing_activities=0,
                dry_run=False,
            ),
        )
        self.assertEqual(
            UserActivity.objects.filter(user=user, action=UserActivity.Action.VPN_REPAIR_EVENT).count(),
            2,
        )

    @patch("apps.legacy_sync.services._fetch_amonora_vpn_repair_events")
    def test_import_amonora_vpn_repair_events_is_idempotent(self, fetch_mock):
        user = User.objects.create_user(
            username="amonora-18",
            email="amonora-18@infinda.local",
            password="pass-123",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 2,
                "legacy_user_id": 18,
                "result": "success",
                "reason": "manual_repair",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 23, 1, 40, 14)),
            }
        ]

        first_summary = import_amonora_vpn_repair_events(database_name="legacy_restore")
        second_summary = import_amonora_vpn_repair_events(database_name="legacy_restore")

        self.assertEqual(first_summary.created_activities, 1)
        self.assertEqual(second_summary.created_activities, 0)
        self.assertEqual(UserActivity.objects.filter(user=user).count(), 1)

    @patch("apps.legacy_sync.services._fetch_amonora_vpn_repair_events")
    def test_import_amonora_vpn_repair_events_supports_dry_run(self, fetch_mock):
        user = User.objects.create_user(
            username="amonora-18",
            email="amonora-18@infinda.local",
            password="pass-123",
        )
        fetch_mock.return_value = [
            {
                "legacy_id": 2,
                "legacy_user_id": 18,
                "result": "success",
                "reason": "manual_repair",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 23, 1, 40, 14)),
            }
        ]

        summary = import_amonora_vpn_repair_events(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraVpnRepairImportSummary(
                source_events=1,
                created_activities=0,
                skipped_missing_users=0,
                skipped_existing_activities=0,
                dry_run=True,
            ),
        )
        self.assertEqual(UserActivity.objects.filter(user=user).count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_vpn_repair_events.import_amonora_vpn_repair_events")
    def test_management_command_prints_vpn_repair_summary(self, import_mock):
        import_mock.return_value = AmonoraVpnRepairImportSummary(
            source_events=2,
            created_activities=2,
            skipped_missing_users=0,
            skipped_existing_activities=0,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_vpn_repair_events",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("created_activities=2", output)

    @patch("apps.legacy_sync.services._fetch_amonora_support_messages")
    @patch("apps.legacy_sync.services._fetch_amonora_support_tickets")
    def test_import_amonora_support_creates_conversations_messages_and_attachments(
        self,
        tickets_mock,
        messages_mock,
    ):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        User.objects.create_user(
            username="amonora-2",
            email="amonora-2@infinda.local",
            password="pass-123",
        )
        TelegramAccountLink.objects.create(
            user=User.objects.get(username="amonora-1"),
            telegram_user_id=1050507766,
            telegram_username="vehsigian",
            telegram_full_name="Diablo",
        )
        TelegramAccountLink.objects.create(
            user=User.objects.get(username="amonora-2"),
            telegram_user_id=6390220658,
            telegram_username="A8449",
            telegram_full_name="yy",
        )
        tickets_mock.return_value = [
            {
                "id": 1,
                "user_id": 1050507766,
                "username": "vehsigian",
                "full_name": "Diablo",
                "status": "closed",
                "assigned_admin_id": 7650618403,
                "assigned_admin_name": "Dexus @dextrmed",
                "last_message_preview": "просто так",
                "last_user_message_preview": "Почему отклонили платеж ?",
                "last_admin_reply_preview": "просто так",
                "admin_cards_json": '{"7650618403": [20], "548589949": [48]}',
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "updated_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 11, 20, 28)),
                "closed_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 11, 20, 28)),
            },
            {
                "id": 2,
                "user_id": 6390220658,
                "username": "A8449",
                "full_name": "yy",
                "status": "in_progress",
                "assigned_admin_id": 548589949,
                "assigned_admin_name": "Ruslan Ix@n @IxcanRuslan",
                "last_message_preview": "Доступ продлён✅",
                "last_user_message_preview": "？",
                "last_admin_reply_preview": "Доступ продлён✅",
                "admin_cards_json": '{"7650618403": [1780], "548589949": [1781]}',
                "created_at": timezone.make_aware(timezone.datetime(2026, 4, 16, 10, 1, 37)),
                "updated_at": timezone.make_aware(timezone.datetime(2026, 4, 21, 11, 53, 18)),
                "closed_at": timezone.make_aware(timezone.datetime(2026, 4, 21, 11, 53, 18)),
            },
        ]
        messages_mock.return_value = [
            {
                "legacy_id": 1,
                "ticket_id": 1,
                "role": "user",
                "sender_id": 1050507766,
                "sender_name": "Diablo",
                "content_type": "ContentType.TEXT",
                "text": "Тест",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "attachment_file_id": "",
                "attachment_file_unique_id": "",
                "attachment_kind": "",
                "attachment_name": "",
                "attachment_mime_type": "",
                "attachment_size": 0,
            },
            {
                "legacy_id": 2,
                "ticket_id": 1,
                "role": "admin",
                "sender_id": 7650618403,
                "sender_name": "Рудольф @dextrmed",
                "content_type": "ContentType.TEXT",
                "text": "тест",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 41)),
                "attachment_file_id": "",
                "attachment_file_unique_id": "",
                "attachment_kind": "",
                "attachment_name": "",
                "attachment_mime_type": "",
                "attachment_size": 0,
            },
            {
                "legacy_id": 3,
                "ticket_id": 2,
                "role": "user",
                "sender_id": 6390220658,
                "sender_name": "yy",
                "content_type": "ContentType.TEXT",
                "text": "Здравствуйте не работает ИНЕЕЕТ",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 17, 0, 37)),
                "attachment_file_id": "file-123",
                "attachment_file_unique_id": "file-uniq-123",
                "attachment_kind": "photo",
                "attachment_name": "screenshot.jpg",
                "attachment_mime_type": "image/jpeg",
                "attachment_size": 128,
            },
        ]

        summary = import_amonora_support(database_name="legacy_restore")

        self.assertEqual(
            summary,
            AmonoraSupportImportSummary(
                source_tickets=2,
                created_conversations=2,
                created_messages=3,
                created_attachments=1,
                created_support_admins=2,
                closed_conversations=1,
                in_progress_conversations=1,
                skipped_missing_users=0,
                skipped_existing_conversations=0,
                dry_run=False,
            ),
        )
        self.assertEqual(SupportConversation.objects.count(), 2)
        self.assertEqual(SupportMessage.objects.count(), 3)
        self.assertEqual(SupportAttachment.objects.count(), 1)
        first_conversation = SupportConversation.objects.get(user__username="amonora-1")
        self.assertEqual(first_conversation.status, SupportConversation.Status.CLOSED)
        self.assertIsNotNone(first_conversation.assigned_admin)
        self.assertEqual(first_conversation.messages.count(), 2)

    @patch("apps.legacy_sync.services._fetch_amonora_support_messages")
    @patch("apps.legacy_sync.services._fetch_amonora_support_tickets")
    def test_import_amonora_support_is_idempotent(self, tickets_mock, messages_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        TelegramAccountLink.objects.create(
            user=User.objects.get(username="amonora-1"),
            telegram_user_id=1050507766,
            telegram_username="vehsigian",
            telegram_full_name="Diablo",
        )
        tickets_mock.return_value = [
            {
                "id": 1,
                "user_id": 1050507766,
                "username": "vehsigian",
                "full_name": "Diablo",
                "status": "closed",
                "assigned_admin_id": 7650618403,
                "assigned_admin_name": "Dexus @dextrmed",
                "last_message_preview": "просто так",
                "last_user_message_preview": "Почему отклонили платеж ?",
                "last_admin_reply_preview": "просто так",
                "admin_cards_json": '{"7650618403": [20], "548589949": [48]}',
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "updated_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 11, 20, 28)),
                "closed_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 11, 20, 28)),
            }
        ]
        messages_mock.return_value = [
            {
                "legacy_id": 1,
                "ticket_id": 1,
                "role": "user",
                "sender_id": 1050507766,
                "sender_name": "Diablo",
                "content_type": "ContentType.TEXT",
                "text": "Тест",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "attachment_file_id": "",
                "attachment_file_unique_id": "",
                "attachment_kind": "",
                "attachment_name": "",
                "attachment_mime_type": "",
                "attachment_size": 0,
            }
        ]

        first_summary = import_amonora_support(database_name="legacy_restore")
        second_summary = import_amonora_support(database_name="legacy_restore")

        self.assertEqual(first_summary.created_conversations, 1)
        self.assertEqual(second_summary.created_conversations, 0)
        self.assertEqual(SupportConversation.objects.count(), 1)
        self.assertEqual(SupportMessage.objects.count(), 1)

    @patch("apps.legacy_sync.services._fetch_amonora_support_messages")
    @patch("apps.legacy_sync.services._fetch_amonora_support_tickets")
    def test_import_amonora_support_supports_dry_run(self, tickets_mock, messages_mock):
        User.objects.create_user(
            username="amonora-1",
            email="amonora-1@infinda.local",
            password="pass-123",
        )
        TelegramAccountLink.objects.create(
            user=User.objects.get(username="amonora-1"),
            telegram_user_id=1050507766,
            telegram_username="vehsigian",
            telegram_full_name="Diablo",
        )
        tickets_mock.return_value = [
            {
                "id": 1,
                "user_id": 1050507766,
                "username": "vehsigian",
                "full_name": "Diablo",
                "status": "closed",
                "assigned_admin_id": 7650618403,
                "assigned_admin_name": "Dexus @dextrmed",
                "last_message_preview": "просто так",
                "last_user_message_preview": "Почему отклонили платеж ?",
                "last_admin_reply_preview": "просто так",
                "admin_cards_json": '{"7650618403": [20], "548589949": [48]}',
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "updated_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 11, 20, 28)),
                "closed_at": timezone.make_aware(timezone.datetime(2026, 3, 17, 11, 20, 28)),
            }
        ]
        messages_mock.return_value = [
            {
                "legacy_id": 1,
                "ticket_id": 1,
                "role": "user",
                "sender_id": 1050507766,
                "sender_name": "Diablo",
                "content_type": "ContentType.TEXT",
                "text": "Тест",
                "created_at": timezone.make_aware(timezone.datetime(2026, 3, 16, 0, 51, 20)),
                "attachment_file_id": "",
                "attachment_file_unique_id": "",
                "attachment_kind": "",
                "attachment_name": "",
                "attachment_mime_type": "",
                "attachment_size": 0,
            }
        ]

        summary = import_amonora_support(database_name="legacy_restore", dry_run=True)

        self.assertEqual(
            summary,
            AmonoraSupportImportSummary(
                source_tickets=1,
                created_conversations=1,
                created_messages=1,
                created_attachments=0,
                created_support_admins=1,
                closed_conversations=1,
                in_progress_conversations=0,
                skipped_missing_users=0,
                skipped_existing_conversations=0,
                dry_run=True,
            ),
        )
        self.assertEqual(SupportConversation.objects.count(), 0)

    @patch("apps.legacy_sync.management.commands.import_amonora_support.import_amonora_support")
    def test_management_command_prints_support_import_summary(self, import_mock):
        import_mock.return_value = AmonoraSupportImportSummary(
            source_tickets=2,
            created_conversations=2,
            created_messages=3,
            created_attachments=1,
            created_support_admins=2,
            closed_conversations=1,
            in_progress_conversations=1,
            skipped_missing_users=0,
            skipped_existing_conversations=0,
            dry_run=False,
        )

        stdout = StringIO()
        call_command(
            "import_amonora_support",
            "--database-name",
            "legacy_restore",
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("database=legacy_restore", output)
        self.assertIn("created_messages=3", output)
        self.assertIn("created_attachments=1", output)
