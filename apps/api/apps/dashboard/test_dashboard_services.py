from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.activity.models import UserActivity
from apps.devices.models import Device
from apps.subscription.models import Subscription, SubscriptionPayment
from apps.support.models import SupportConversation, SupportMessage

from .services import build_admin_dashboard_context


User = get_user_model()


class DashboardServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard-user",
            email="dashboard@example.com",
            password="dashboard-pass-123",
        )
        self.admin_user = User.objects.create_user(
            username="dashboard-admin",
            email="dashboard-admin@example.com",
            password="dashboard-pass-123",
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=10),
            max_devices=3,
            public_token="dashboard-public-token",
            main_url="https://infinda.example/sub/main",
        )
        self.payment = SubscriptionPayment.objects.create(
            user=self.user,
            plan_code="1m",
            plan_name="1 месяц",
            amount_rub=149,
            duration_days=30,
            max_devices=3,
            provider=SubscriptionPayment.PROVIDER_PLATEGA,
            payment_method="sbp",
            status=SubscriptionPayment.STATUS_PENDING,
        )
        self.conversation = SupportConversation.objects.create(
            user=self.user,
            status=SupportConversation.Status.NEW,
        )
        SupportMessage.objects.create(
            conversation=self.conversation,
            sender_type=SupportMessage.SenderType.ADMIN,
            sender_user=self.admin_user,
            sender_display_name="Support Admin",
            source=SupportMessage.Source.ADMIN,
            text="Ответ поддержки",
        )
        Device.objects.create(
            user=self.user,
            name="Work laptop",
            display_name="Work laptop",
            icon=Device.Icon.LAPTOP,
            ip_address="127.0.0.1",
            last_seen=timezone.now() - timedelta(days=8),
            status=Device.Status.STALE,
            platform_name="Windows",
            platform="Windows",
            client_name="v2rayN",
            client="v2rayN",
        )
        UserActivity.objects.create(
            user=self.user,
            action=UserActivity.Action.LOGIN,
            description="Пользователь вошел в систему.",
        )

    def test_build_admin_dashboard_context_collects_key_sections(self):
        context = build_admin_dashboard_context()

        self.assertIn("admin_dashboard_cards", context)
        self.assertEqual(len(context["admin_dashboard_cards"]), 6)
        self.assertTrue(context["admin_dashboard_recent_payments"])
        self.assertTrue(context["admin_dashboard_recent_activities"])
        self.assertTrue(context["admin_dashboard_support_events"])
        self.assertTrue(context["admin_dashboard_problem_payments"])
        self.assertTrue(context["admin_dashboard_device_alerts"])
        self.assertEqual(context["admin_dashboard_attention_stats"]["problem_payments_count"], 1)
        self.assertEqual(context["admin_dashboard_attention_stats"]["new_tickets_count"], 1)
        self.assertEqual(context["admin_dashboard_attention_stats"]["device_alerts_count"], 1)
