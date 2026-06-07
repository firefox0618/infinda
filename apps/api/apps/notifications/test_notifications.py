from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.telegram.models import TelegramAccountLink

from .models import Notification
from .services import dispatch_notification


User = get_user_model()


class NotificationDispatchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notify-user",
            email="notify@example.com",
            password="notify-pass-123",
        )

    @patch("apps.telegram.services.send_telegram_message")
    def test_dispatch_notification_sends_telegram_message(self, send_telegram_message_mock):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_username="notify_user",
            telegram_full_name="Notify User",
            is_active=True,
        )

        notification = dispatch_notification(
            event_type=Notification.EVENT_PAYMENT_PAID,
            user=self.user,
            payload={"plan_name": "3 месяца", "amount_rub": 399, "active_until": "2026-12-01"},
        )

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_SENT)
        self.assertIsNotNone(notification.sent_at)
        send_telegram_message_mock.assert_called_once()

    def test_dispatch_notification_marks_skipped_without_telegram_link(self):
        notification = dispatch_notification(
            event_type=Notification.EVENT_TELEGRAM_LINKED,
            user=self.user,
            payload={},
        )

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_SKIPPED)

    @patch("apps.telegram.services.send_telegram_message", side_effect=RuntimeError("telegram offline"))
    def test_dispatch_notification_marks_failed_on_transport_error(self, _send_telegram_message_mock):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_username="notify_user",
            telegram_full_name="Notify User",
            is_active=True,
        )

        notification = dispatch_notification(
            event_type=Notification.EVENT_DEVICE_REVOKED,
            user=self.user,
            payload={"display_name": "MacBook"},
        )

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_FAILED)
        self.assertIsNotNone(notification.failed_at)
