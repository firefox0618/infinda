from datetime import timedelta
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

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

    def send_message(self, *, chat_id: int, text: str) -> None:
        self.sent_messages.append(
            {
                "chat_id": chat_id,
                "text": text,
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
        self.assertEqual(
            self.client.sent_messages[-1]["text"],
            "Сообщение передано в поддержку INFINDA.",
        )
