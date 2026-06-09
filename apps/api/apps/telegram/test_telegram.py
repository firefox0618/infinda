from datetime import timedelta
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.devices.models import Device
from apps.provisioning.models import ProvisioningOperation
from apps.subscription.models import Subscription, SubscriptionRoute
from apps.routing.services import ensure_default_route_catalog, get_connection_route_by_code
from apps.support.models import SupportConversation

from .bot_runtime import process_telegram_update
from .models import TelegramAccountLink, TelegramLinkToken
from .services import create_telegram_link_token


User = get_user_model()


@override_settings(TELEGRAM_MAIN_BOT_USERNAME="infinda_test_bot")
class TelegramLinkApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="telegram-user",
            email="telegram@example.com",
            password="telegram-pass-123",
        )
        self.other_user = User.objects.create_user(
            username="telegram-other",
            email="telegram-other@example.com",
            password="telegram-pass-123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_link_status_returns_empty_state(self):
        response = self.client.get("/api/telegram/link/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_linked"], False)
        self.assertIsNone(response.data["telegram_user_id"])

    def test_create_link_token_returns_deep_link(self):
        response = self.client.post("/api/telegram/link/")

        self.assertEqual(response.status_code, 201)
        self.assertIn("https://t.me/infinda_test_bot?start=link_", response.data["deep_link_url"])
        self.assertTrue(TelegramLinkToken.objects.filter(user=self.user).exists())

    def test_confirm_link_activates_telegram_binding(self):
        token_response = self.client.post("/api/telegram/link/")
        token = token_response.data["token"]

        confirm_response = self.client.post(
            "/api/telegram/link/confirm/",
            {
                "token": token,
                "telegram_user_id": 123456789,
                "telegram_username": "demo_user",
                "telegram_full_name": "Demo User",
            },
            format="json",
        )

        self.assertEqual(confirm_response.status_code, 200)
        link = TelegramAccountLink.objects.get(user=self.user)
        self.assertEqual(link.telegram_user_id, 123456789)
        self.assertEqual(link.telegram_username, "demo_user")

    def test_confirm_link_rejects_expired_token(self):
        token_response = self.client.post("/api/telegram/link/")
        token = TelegramLinkToken.objects.get(token=token_response.data["token"])
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at", "updated_at"])

        response = self.client.post(
            "/api/telegram/link/confirm/",
            {
                "token": token.token,
                "telegram_user_id": 123456789,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")

    def test_confirm_link_rejects_reused_telegram_account(self):
        TelegramAccountLink.objects.create(
            user=self.other_user,
            telegram_user_id=987654321,
            telegram_username="busy_user",
            telegram_full_name="Busy User",
        )
        token_response = self.client.post("/api/telegram/link/")

        response = self.client.post(
            "/api/telegram/link/confirm/",
            {
                "token": token_response.data["token"],
                "telegram_user_id": 987654321,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")

    def test_delete_link_marks_binding_inactive(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=111111,
            telegram_username="linked_user",
            telegram_full_name="Linked User",
        )

        response = self.client.delete("/api/telegram/link/")

        self.assertEqual(response.status_code, 200)
        link = TelegramAccountLink.objects.get(user=self.user)
        self.assertFalse(link.is_active)


class FakeTelegramBotClient:
    def __init__(self):
        self.sent_messages: list[dict] = []
        self.sent_documents: list[dict] = []
        self.files = {
            "document-file-id": {
                "file_path": "documents/support-log.txt",
            },
        }
        self.downloads = {
            "documents/support-log.txt": b"support-log",
        }

    def send_message(self, *, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        self.sent_messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
            }
        )

    def send_document(
        self,
        *,
        chat_id: int,
        file_name: str,
        content_bytes: bytes,
        caption: str | None = None,
    ) -> None:
        self.sent_documents.append(
            {
                "chat_id": chat_id,
                "file_name": file_name,
                "content_bytes": content_bytes,
                "caption": caption,
            }
        )

    def get_file(self, *, file_id: str) -> dict:
        return self.files[file_id]

    def download_file(self, *, file_path: str) -> bytes:
        return self.downloads[file_path]


@override_settings(TELEGRAM_MAIN_BOT_USERNAME="infinda_test_bot")
class TelegramBotRuntimeTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media_dir = tempfile.TemporaryDirectory()
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media_dir.name)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        cls._temp_media_dir.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.client = FakeTelegramBotClient()
        self.user = User.objects.create_user(
            username="bot-user",
            email="bot-user@example.com",
            password="telegram-pass-123",
        )
        ensure_default_route_catalog()

    def test_process_start_link_confirms_binding(self):
        token = create_telegram_link_token(
            user=self.user,
            bot_username="infinda_test_bot",
        )

        process_telegram_update(
            update={
                "update_id": 1,
                "message": {
                    "chat": {"id": 9001},
                    "from": {
                        "id": 123456789,
                        "username": "linked_user",
                        "first_name": "Linked",
                        "last_name": "User",
                    },
                    "text": f"/start link_{token.token}",
                },
            },
            client=self.client,
        )

        link = TelegramAccountLink.objects.get(user=self.user)
        self.assertEqual(link.telegram_user_id, 123456789)
        self.assertEqual(link.telegram_username, "linked_user")
        self.assertEqual(
            self.client.sent_messages[-1]["text"],
            "Telegram успешно привязан. Теперь можно писать сюда сообщения для поддержки INFINDA.",
        )

    def test_process_message_creates_support_conversation_for_linked_user(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=777000,
            telegram_username="runtime_user",
            telegram_full_name="Runtime User",
        )

        process_telegram_update(
            update={
                "update_id": 2,
                "message": {
                    "chat": {"id": 9002},
                    "from": {
                        "id": 777000,
                        "username": "runtime_user",
                        "first_name": "Runtime",
                        "last_name": "User",
                    },
                    "caption": "Нужна помощь по подписке",
                    "document": {
                        "file_id": "document-file-id",
                        "file_name": "support-log.txt",
                        "mime_type": "text/plain",
                    },
                },
            },
            client=self.client,
        )

        conversation = SupportConversation.objects.get(user=self.user)
        self.assertEqual(conversation.status, SupportConversation.Status.NEW)
        message = conversation.messages.get()
        self.assertEqual(message.source, "telegram_support_bot")
        self.assertEqual(message.sender_display_name, "Runtime User (@runtime_user)")
        self.assertEqual(message.text, "Нужна помощь по подписке")
        self.assertEqual(message.attachments.count(), 1)
        self.assertEqual(message.attachments.first().file_name, "support-log.txt")

    def test_start_for_linked_user_returns_main_menu(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700001,
            telegram_username="menu_user",
            telegram_full_name="Menu User",
        )

        process_telegram_update(
            update={
                "update_id": 3,
                "message": {
                    "chat": {"id": 9100},
                    "from": {
                        "id": 700001,
                        "username": "menu_user",
                        "first_name": "Menu",
                        "last_name": "User",
                    },
                    "text": "/start",
                },
            },
            client=self.client,
        )

        self.assertIn("INFINDA bot подключен", self.client.sent_messages[-1]["text"])
        self.assertIn("/subscription", self.client.sent_messages[-1]["text"])
        self.assertIsNotNone(self.client.sent_messages[-1]["reply_markup"])

    def test_start_for_unlinked_user_returns_link_help_keyboard(self):
        process_telegram_update(
            update={
                "update_id": 11,
                "message": {
                    "chat": {"id": 9108},
                    "from": {
                        "id": 800001,
                        "username": "unlinked_user",
                        "first_name": "Unlinked",
                        "last_name": "User",
                    },
                    "text": "/start",
                },
            },
            client=self.client,
        )

        self.assertIn("Этот бот принимает сообщения в поддержку", self.client.sent_messages[-1]["text"])
        self.assertIsNotNone(self.client.sent_messages[-1]["reply_markup"])

    def test_subscription_menu_button_routes_to_subscription_summary(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=800002,
            telegram_username="button_user",
            telegram_full_name="Button User",
        )
        route = get_connection_route_by_code(code="ru")
        subscription = Subscription.objects.create(
            user=self.user,
            plan_name="6 месяцев",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=180),
            max_devices=5,
            public_token="telegram-token-4",
            main_url="https://infinda.com/sub/telegram-token-4",
        )
        SubscriptionRoute.objects.create(
            subscription=subscription,
            code="ru",
            label="Россия",
            url=route.endpoint_url,
            position=1,
            connection_route=route,
        )

        process_telegram_update(
            update={
                "update_id": 12,
                "message": {
                    "chat": {"id": 9109},
                    "from": {
                        "id": 800002,
                        "username": "button_user",
                        "first_name": "Button",
                        "last_name": "User",
                    },
                    "text": "Подписка",
                },
            },
            client=self.client,
        )

        self.assertIn("Подписка: 6 месяцев", self.client.sent_messages[-1]["text"])

    def test_link_help_button_returns_onboarding_hint(self):
        process_telegram_update(
            update={
                "update_id": 13,
                "message": {
                    "chat": {"id": 9110},
                    "from": {
                        "id": 800003,
                        "username": "help_user",
                        "first_name": "Help",
                        "last_name": "User",
                    },
                    "text": "Как привязать Telegram",
                },
            },
            client=self.client,
        )

        self.assertIn("Чтобы использовать INFINDA bot как личный кабинет", self.client.sent_messages[-1]["text"])

    def test_subscription_command_returns_real_subscription_summary(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700002,
            telegram_username="subscription_user",
            telegram_full_name="Subscription User",
        )
        route = get_connection_route_by_code(code="ru")
        subscription = Subscription.objects.create(
            user=self.user,
            plan_name="3 месяца",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=90),
            max_devices=4,
            public_token="telegram-token-1",
            main_url="https://infinda.com/sub/telegram-token-1",
        )
        SubscriptionRoute.objects.create(
            subscription=subscription,
            code="ru",
            label="Россия",
            url=route.endpoint_url,
            position=1,
            connection_route=route,
        )

        process_telegram_update(
            update={
                "update_id": 4,
                "message": {
                    "chat": {"id": 9101},
                    "from": {
                        "id": 700002,
                        "username": "subscription_user",
                        "first_name": "Subscription",
                        "last_name": "User",
                    },
                    "text": "/subscription",
                },
            },
            client=self.client,
        )

        self.assertIn("Подписка: 3 месяца", self.client.sent_messages[-1]["text"])
        self.assertIn("Маршрутов: 1", self.client.sent_messages[-1]["text"])

    def test_devices_command_returns_real_devices_summary(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700003,
            telegram_username="devices_user",
            telegram_full_name="Devices User",
        )
        Device.objects.create(
            user=self.user,
            name="MacBook",
            display_name="MacBook",
            icon=Device.Icon.LAPTOP,
            ip_address="203.0.113.101",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="macOS",
            platform="macOS",
            client_name="Happ",
            client="Happ",
        )

        process_telegram_update(
            update={
                "update_id": 5,
                "message": {
                    "chat": {"id": 9102},
                    "from": {
                        "id": 700003,
                        "username": "devices_user",
                        "first_name": "Devices",
                        "last_name": "User",
                    },
                    "text": "/devices",
                },
            },
            client=self.client,
        )

        self.assertIn("Ваши устройства:", self.client.sent_messages[-1]["text"])
        self.assertIn("MacBook", self.client.sent_messages[-1]["text"])
        self.assertIn("active", self.client.sent_messages[-1]["text"])

    def test_support_command_returns_product_hint(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700004,
            telegram_username="support_user",
            telegram_full_name="Support User",
        )

        process_telegram_update(
            update={
                "update_id": 6,
                "message": {
                    "chat": {"id": 9103},
                    "from": {
                        "id": 700004,
                        "username": "support_user",
                        "first_name": "Support",
                        "last_name": "User",
                    },
                    "text": "/support",
                },
            },
            client=self.client,
        )

        self.assertIn("Напишите сообщение прямо в этот чат", self.client.sent_messages[-1]["text"])

    def test_plans_command_returns_catalog_hint(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700005,
            telegram_username="plans_user",
            telegram_full_name="Plans User",
        )

        process_telegram_update(
            update={
                "update_id": 7,
                "message": {
                    "chat": {"id": 9104},
                    "from": {
                        "id": 700005,
                        "username": "plans_user",
                        "first_name": "Plans",
                        "last_name": "User",
                    },
                    "text": "/plans",
                },
            },
            client=self.client,
        )

        self.assertIn("Доступные тарифы:", self.client.sent_messages[-1]["text"])
        self.assertIn("/buy 3m", self.client.sent_messages[-1]["text"])

    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
    )
    @patch(
        "apps.subscription.services.PlategaClient.create_payment",
        return_value=SimpleNamespace(
            transaction_id="plat-telegram-buy-100",
            checkout_url="https://pay.platega.example/plat-telegram-buy-100",
            status="PENDING",
            raw={
                "transactionId": "plat-telegram-buy-100",
                "redirect": "https://pay.platega.example/plat-telegram-buy-100",
                "status": "PENDING",
            },
        ),
    )
    def test_buy_command_returns_checkout_link(self, mocked_create_payment):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700006,
            telegram_username="buy_user",
            telegram_full_name="Buy User",
        )

        process_telegram_update(
            update={
                "update_id": 8,
                "message": {
                    "chat": {"id": 9105},
                    "from": {
                        "id": 700006,
                        "username": "buy_user",
                        "first_name": "Buy",
                        "last_name": "User",
                    },
                    "text": "/buy 3m",
                },
            },
            client=self.client,
        )

        mocked_create_payment.assert_called_once()
        self.assertIn("Ссылка на оплату тарифа 3 месяца:", self.client.sent_messages[-1]["text"])
        self.assertIn("https://pay.platega.example/plat-telegram-buy-100", self.client.sent_messages[-1]["text"])

    def test_sync_command_runs_manual_subscription_sync(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700007,
            telegram_username="sync_user",
            telegram_full_name="Sync User",
        )
        route = get_connection_route_by_code(code="ru")
        subscription = Subscription.objects.create(
            user=self.user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="telegram-token-2",
            main_url="https://infinda.com/sub/telegram-token-2",
        )
        SubscriptionRoute.objects.create(
            subscription=subscription,
            code="ru",
            label="Россия",
            url=route.endpoint_url,
            position=1,
            connection_route=route,
        )

        process_telegram_update(
            update={
                "update_id": 9,
                "message": {
                    "chat": {"id": 9106},
                    "from": {
                        "id": 700007,
                        "username": "sync_user",
                        "first_name": "Sync",
                        "last_name": "User",
                    },
                    "text": "/sync",
                },
            },
            client=self.client,
        )

        self.assertIn("Синхронизация доступа запущена.", self.client.sent_messages[-1]["text"])
        self.assertEqual(
            ProvisioningOperation.objects.filter(
                user=self.user,
                subscription=subscription,
                trigger=ProvisioningOperation.Trigger.MANUAL_SYNC,
            ).count(),
            1,
        )

    def test_repair_command_runs_device_repair(self):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=700008,
            telegram_username="repair_user",
            telegram_full_name="Repair User",
        )
        route = get_connection_route_by_code(code="ru")
        subscription = Subscription.objects.create(
            user=self.user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="telegram-token-3",
            main_url="https://infinda.com/sub/telegram-token-3",
        )
        SubscriptionRoute.objects.create(
            subscription=subscription,
            code="ru",
            label="Россия",
            url=route.endpoint_url,
            position=1,
            connection_route=route,
        )
        device = Device.objects.create(
            user=self.user,
            name="Repair Laptop",
            display_name="Repair Laptop",
            icon=Device.Icon.LAPTOP,
            ip_address="203.0.113.120",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="Linux",
            platform="Linux",
            client_name="Happ",
            client="Happ",
        )

        process_telegram_update(
            update={
                "update_id": 10,
                "message": {
                    "chat": {"id": 9107},
                    "from": {
                        "id": 700008,
                        "username": "repair_user",
                        "first_name": "Repair",
                        "last_name": "User",
                    },
                    "text": f"/repair {device.id}",
                },
            },
            client=self.client,
        )

        self.assertIn("Восстановление устройства", self.client.sent_messages[-1]["text"])
        self.assertEqual(
            ProvisioningOperation.objects.filter(
                user=self.user,
                subscription=subscription,
                device=device,
                trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
            ).count(),
            1,
        )
