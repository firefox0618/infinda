import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.activity.models import UserActivity
from apps.devices.models import Device
from apps.subscription.models import Subscription, SubscriptionPayment
from apps.telegram.models import TelegramAccountLink

from .models import SupportConversation
from .services import (
    IncomingSupportAttachment,
    close_support_conversation,
    create_support_message_from_admin,
    create_support_message_from_telegram,
    create_support_message_from_user,
    ensure_support_conversation_admin_access,
    reply_to_support_conversation,
)


User = get_user_model()


class SupportApiTests(APITestCase):
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
        self.user = User.objects.create_user(
            username="support-user",
            email="support@example.com",
            password="support-pass-123",
        )
        self.admin_user = User.objects.create_superuser(
            username="support-admin",
            email="support-admin@example.com",
            password="support-pass-123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_conversation_returns_empty_dialog_for_new_user(self):
        response = self.client.get("/api/support/conversation/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "new")
        self.assertEqual(response.data["messages"], [])

    def test_post_message_creates_conversation_and_message(self):
        uploaded_file = SimpleUploadedFile(
            "screen.txt",
            b"demo-screen",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/support/messages/",
            {
                "text": "Не могу подключить устройство",
                "attachments": [uploaded_file],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "new")
        self.assertEqual(len(response.data["messages"]), 1)
        self.assertEqual(response.data["messages"][0]["sender_type"], "user")
        self.assertEqual(response.data["messages"][0]["attachments"][0]["file_name"], "screen.txt")

    def test_post_message_requires_text_or_attachment(self):
        response = self.client.post(
            "/api/support/messages/",
            {"text": ""},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")

    def test_user_message_reopens_closed_conversation(self):
        response = self.client.post(
            "/api/support/messages/",
            {"text": "Первое сообщение"},
            format="multipart",
        )
        conversation = SupportConversation.objects.get(pk=response.data["id"])
        close_support_conversation(conversation=conversation)

        reopen_response = self.client.post(
            "/api/support/messages/",
            {"text": "Новый вопрос"},
            format="multipart",
        )

        self.assertEqual(reopen_response.status_code, 201)
        self.assertEqual(reopen_response.data["status"], "new")

    def test_admin_reply_moves_conversation_to_in_progress(self):
        self.client.post(
            "/api/support/messages/",
            {"text": "Первое сообщение"},
            format="multipart",
        )
        conversation = SupportConversation.objects.get(user=self.user)

        create_support_message_from_admin(
            admin_user=self.admin_user,
            conversation=conversation,
            text="Проверяем доступ и скоро ответим.",
        )

        conversation.refresh_from_db()
        self.assertEqual(conversation.status, SupportConversation.Status.IN_PROGRESS)
        self.assertEqual(conversation.assigned_admin, self.admin_user)
        self.assertEqual(conversation.messages.count(), 2)

    def test_admin_reply_can_include_attachments(self):
        self.client.post(
            "/api/support/messages/",
            {"text": "Нужен файл в ответе"},
            format="multipart",
        )
        conversation = SupportConversation.objects.get(user=self.user)
        uploaded_file = SimpleUploadedFile(
            "answer.txt",
            b"support-answer",
            content_type="text/plain",
        )

        message = create_support_message_from_admin(
            admin_user=self.admin_user,
            conversation=conversation,
            text="Прикладываем файл с инструкцией.",
            attachments=[uploaded_file],
        )

        self.assertEqual(message.attachments.count(), 1)
        self.assertEqual(message.attachments.first().file_name, "answer.txt")

    def test_reply_to_support_conversation_assigns_admin_and_can_close(self):
        self.client.post(
            "/api/support/messages/",
            {"text": "Нужен быстрый ответ"},
            format="multipart",
        )
        conversation = SupportConversation.objects.get(user=self.user)

        updated_conversation = reply_to_support_conversation(
            admin_user=self.admin_user,
            conversation=conversation,
            text="Берем в работу и закрываем после ответа.",
            assign_to_admin=True,
            close_after_reply=True,
        )

        updated_conversation.refresh_from_db()
        self.assertEqual(updated_conversation.assigned_admin, self.admin_user)
        self.assertEqual(updated_conversation.status, SupportConversation.Status.CLOSED)
        self.assertEqual(updated_conversation.messages.count(), 3)
        self.assertEqual(
            updated_conversation.messages.order_by("-created_at", "-id").first().text,
            "Диалог закрыт. Если появятся новые вопросы, вы можете открыть его новым сообщением.",
        )

    def test_assigned_conversation_blocks_other_admin_reply(self):
        other_admin = User.objects.create_superuser(
            username="support-admin-2",
            email="support-admin-2@example.com",
            password="support-pass-123",
        )
        self.client.post(
            "/api/support/messages/",
            {"text": "Закрепите тикет"},
            format="multipart",
        )
        conversation = SupportConversation.objects.get(user=self.user)
        conversation.assigned_admin = self.admin_user
        conversation.status = SupportConversation.Status.IN_PROGRESS
        conversation.save(update_fields=["assigned_admin", "status", "updated_at"])

        with self.assertRaises(ValidationError):
            ensure_support_conversation_admin_access(
                conversation=conversation,
                admin_user=other_admin,
            )

        with self.assertRaises(ValidationError):
            reply_to_support_conversation(
                admin_user=other_admin,
                conversation=conversation,
                text="Я отвечу вместо назначенного оператора.",
            )

    def test_create_message_from_telegram_creates_support_message_with_attachment(self):
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@telegram_user)",
            text="Проблема сохраняется и в Telegram.",
            attachments=[
                IncomingSupportAttachment(
                    file_name="telegram-log.txt",
                    content_type="text/plain",
                    content_bytes=b"vpn-log",
                ),
            ],
            telegram_user_id=123456789,
        )

        self.assertEqual(conversation.messages.count(), 1)
        message = conversation.messages.first()
        self.assertEqual(message.source, "telegram_support_bot")
        self.assertEqual(message.sender_display_name, "Telegram User (@telegram_user)")
        self.assertEqual(message.attachments.count(), 1)
        self.assertEqual(message.attachments.first().file_name, "telegram-log.txt")

    @patch("apps.support.services.notify_support_team_about_ticket")
    def test_new_web_ticket_notifies_support_team(self, notify_support_team_about_ticket):
        self.client.post(
            "/api/support/messages/",
            {"text": "Новая проблема со входом"},
            format="multipart",
        )

        notify_support_team_about_ticket.assert_called_once()
        self.assertIn("Новый тикет", notify_support_team_about_ticket.call_args.kwargs["text"])
        self.assertIn("Сайт", notify_support_team_about_ticket.call_args.kwargs["text"])

    @patch("apps.support.services.send_telegram_message")
    def test_admin_reply_is_delivered_to_telegram_for_telegram_ticket(self, send_telegram_message):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_username="linked_support_user",
            telegram_full_name="Linked Support User",
        )
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@telegram_user)",
            text="Проблема через Telegram",
            attachments=[],
            telegram_user_id=123456789,
        )

        create_support_message_from_admin(
            admin_user=self.admin_user,
            conversation=conversation,
            text="Проверили настройки, все исправили.",
        )

        send_telegram_message.assert_called_once()
        self.assertEqual(send_telegram_message.call_args.kwargs["chat_id"], 123456789)
        self.assertIn("Ответ по тикету", send_telegram_message.call_args.kwargs["text"])
        self.assertIn("Проверили настройки, все исправили.", send_telegram_message.call_args.kwargs["text"])

    @patch("apps.support.services.send_telegram_document")
    @patch("apps.support.services.send_telegram_message")
    def test_admin_reply_with_attachments_lists_attachment_names_in_telegram_delivery(
        self,
        send_telegram_message,
        send_telegram_document,
    ):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_username="linked_support_user",
            telegram_full_name="Linked Support User",
        )
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@telegram_user)",
            text="Нужен файл через Telegram",
            attachments=[],
            telegram_user_id=123456789,
        )
        uploaded_file = SimpleUploadedFile(
            "guide.txt",
            b"telegram-guide",
            content_type="text/plain",
        )

        create_support_message_from_admin(
            admin_user=self.admin_user,
            conversation=conversation,
            text="Прикладываем гайд.",
            attachments=[uploaded_file],
        )

        send_telegram_message.assert_called_once()
        self.assertIn("Вложения: guide.txt", send_telegram_message.call_args.kwargs["text"])
        send_telegram_document.assert_called_once()
        self.assertEqual(send_telegram_document.call_args.kwargs["file_name"], "guide.txt")

    @patch("apps.support.services.send_telegram_message")
    def test_close_telegram_ticket_sends_closure_notice(self, send_telegram_message):
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_username="linked_support_user",
            telegram_full_name="Linked Support User",
        )
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@telegram_user)",
            text="Закройте после ответа",
            attachments=[],
            telegram_user_id=123456789,
        )
        send_telegram_message.reset_mock()

        close_support_conversation(
            conversation=conversation,
            closed_by=self.admin_user,
        )

        self.assertEqual(send_telegram_message.call_count, 1)
        self.assertEqual(send_telegram_message.call_args.kwargs["chat_id"], 123456789)
        self.assertIn("закрыт", send_telegram_message.call_args.kwargs["text"])
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, SupportConversation.Status.CLOSED)
        self.assertEqual(conversation.messages.count(), 2)

    @patch("apps.support.services.send_telegram_message")
    def test_close_web_ticket_does_not_send_telegram_notice(self, send_telegram_message):
        self.client.post(
            "/api/support/messages/",
            {"text": "Вопрос только с сайта"},
            format="multipart",
        )
        conversation = SupportConversation.objects.get(user=self.user)
        send_telegram_message.reset_mock()

        close_support_conversation(
            conversation=conversation,
            closed_by=self.admin_user,
        )

        send_telegram_message.assert_not_called()


class SupportAdminWorkflowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-support-user",
            email="admin-support-user@example.com",
            password="support-pass-123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin-workflow",
            email="admin-workflow@example.com",
            password="support-pass-123",
        )
        self.other_admin = User.objects.create_superuser(
            username="admin-workflow-2",
            email="admin-workflow-2@example.com",
            password="support-pass-123",
        )
        self.admin_client = Client()
        self.admin_client.force_login(self.admin_user)
        self.request_factory = RequestFactory()

    def build_admin_request(self, *, user):
        request = self.request_factory.post("/admin/")
        request.user = user
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def test_admin_change_page_renders_workflow_blocks(self):
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@workflow_user)",
            text="Покажите это в карточке.",
            attachments=[],
            telegram_user_id=1234567,
        )

        response = self.admin_client.get(
            reverse("admin:support_supportconversation_change", args=[conversation.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сводка по тикету")
        self.assertContains(response, "Быстрые действия оператора")
        self.assertContains(response, "Последнее сообщение пользователя")
        self.assertContains(response, "Telegram")

    @patch("apps.support.services.send_telegram_message")
    def test_admin_can_reply_from_conversation_change_form(self, send_telegram_message):
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@workflow_user)",
            text="Жду ответ в карточке.",
            attachments=[],
            telegram_user_id=1234567,
        )
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=1234567,
            telegram_username="workflow_user",
            telegram_full_name="Workflow User",
        )
        admin_instance = admin.site._registry[SupportConversation]
        request = self.build_admin_request(user=self.admin_user)
        form_class = admin_instance.get_form(request, conversation, change=True)
        form = form_class(
            data={
                "user": str(self.user.id),
                "status": conversation.status,
                "assigned_admin": "",
                "assign_to_me": "on",
                "response_text": "Ответ из карточки admin.",
            },
            files=MultiValueDict(),
            instance=conversation,
        )

        self.assertTrue(form.is_valid(), form.errors)
        admin_instance.save_model(request, conversation, form, change=True)

        conversation.refresh_from_db()
        self.assertEqual(conversation.assigned_admin, self.admin_user)
        self.assertEqual(conversation.status, SupportConversation.Status.IN_PROGRESS)
        self.assertTrue(
            conversation.messages.filter(text="Ответ из карточки admin.").exists()
        )
        send_telegram_message.assert_called_once()

    def test_other_admin_cannot_reply_to_foreign_assigned_conversation_from_change_form(self):
        conversation = create_support_message_from_user(
            user=self.user,
            text="Тикет закреплен за другим оператором.",
            attachments=[],
        )
        conversation.assigned_admin = self.other_admin
        conversation.status = SupportConversation.Status.IN_PROGRESS
        conversation.save(update_fields=["assigned_admin", "status", "updated_at"])
        admin_instance = admin.site._registry[SupportConversation]
        request = self.build_admin_request(user=self.admin_user)
        form_class = admin_instance.get_form(request, conversation, change=True)
        form = form_class(
            data={
                "user": str(self.user.id),
                "status": conversation.status,
                "assigned_admin": str(self.other_admin.id),
                "response_text": "Попытка чужого ответа.",
            },
            files=MultiValueDict(),
            instance=conversation,
        )

        self.assertTrue(form.is_valid(), form.errors)
        admin_instance.save_model(request, conversation, form, change=True)

        conversation.refresh_from_db()
        self.assertFalse(
            conversation.messages.filter(text="Попытка чужого ответа.").exists()
        )
        messages = [message.message for message in get_messages(request)]
        self.assertTrue(any("Диалог уже закреплен" in message for message in messages))

    def test_admin_can_reassign_conversation_to_other_operator_from_change_form(self):
        conversation = create_support_message_from_user(
            user=self.user,
            text="Нужно передать тикет другому оператору.",
            attachments=[],
        )
        conversation.assigned_admin = self.admin_user
        conversation.status = SupportConversation.Status.IN_PROGRESS
        conversation.save(update_fields=["assigned_admin", "status", "updated_at"])

        admin_instance = admin.site._registry[SupportConversation]
        request = self.build_admin_request(user=self.admin_user)
        form_class = admin_instance.get_form(request, conversation, change=True)
        form = form_class(
            data={
                "user": str(self.user.id),
                "status": conversation.status,
                "assigned_admin": str(self.admin_user.id),
                "reassign_to_admin": str(self.other_admin.id),
                "response_text": "",
            },
            files=MultiValueDict(),
            instance=conversation,
        )

        self.assertTrue(form.is_valid(), form.errors)
        admin_instance.save_model(request, conversation, form, change=True)

        conversation.refresh_from_db()
        self.assertEqual(conversation.assigned_admin, self.other_admin)
        messages = [message.message for message in get_messages(request)]
        self.assertTrue(any("Тикет переназначен оператору" in message for message in messages))

    @patch("apps.support.services.send_telegram_document")
    @patch("apps.support.services.send_telegram_message")
    def test_admin_change_form_can_send_reply_with_attachments(
        self,
        send_telegram_message,
        send_telegram_document,
    ):
        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram User (@workflow_user)",
            text="Нужен файл из карточки.",
            attachments=[],
            telegram_user_id=1234567,
        )
        TelegramAccountLink.objects.create(
            user=self.user,
            telegram_user_id=1234567,
            telegram_username="workflow_user",
            telegram_full_name="Workflow User",
        )
        admin_instance = admin.site._registry[SupportConversation]
        request = self.build_admin_request(user=self.admin_user)
        form_class = admin_instance.get_form(request, conversation, change=True)
        uploaded_file = SimpleUploadedFile(
            "card-answer.txt",
            b"admin-card-file",
            content_type="text/plain",
        )
        form = form_class(
            data={
                "user": str(self.user.id),
                "status": conversation.status,
                "assigned_admin": "",
                "assign_to_me": "on",
                "response_text": "Отправляем файл из карточки.",
            },
            files=MultiValueDict({"response_attachments": [uploaded_file]}),
            instance=conversation,
        )

        self.assertTrue(form.is_valid(), form.errors)
        admin_instance.save_model(request, conversation, form, change=True)

        conversation.refresh_from_db()
        reply_message = conversation.messages.order_by("-created_at", "-id").first()
        self.assertEqual(reply_message.attachments.count(), 1)
        self.assertEqual(reply_message.attachments.first().file_name, "card-answer.txt")
        send_telegram_message.assert_called_once()
        self.assertIn("Вложения: card-answer.txt", send_telegram_message.call_args.kwargs["text"])
        send_telegram_document.assert_called_once()
        self.assertEqual(
            send_telegram_document.call_args.kwargs["file_name"],
            "card-answer.txt",
        )


class AdminDashboardWorkspaceTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="dashboard-admin",
            email="dashboard-admin@example.com",
            password="dashboard-pass-123",
        )
        self.user = User.objects.create_user(
            username="dashboard-user",
            email="dashboard-user@example.com",
            password="dashboard-pass-123",
        )
        self.client = Client()
        self.client.force_login(self.admin_user)

        today = timezone.localdate()
        now = timezone.now()

        create_support_message_from_user(
            user=self.user,
            text="Новый тикет для обзора.",
            attachments=[],
        )
        create_support_message_from_admin(
            conversation=self.user.support_conversation,
            admin_user=self.admin_user,
            text="Ответ оператора для ленты.",
            attachments=[],
        )

        Subscription.objects.create(
            user=self.user,
            plan_name="Тестовый план",
            starts_at=today - timedelta(days=10),
            ends_at=today + timedelta(days=3),
            max_devices=3,
            public_token="support-admin-dashboard-token",
            main_url="https://example.com/subscription",
        )
        SubscriptionPayment.objects.create(
            user=self.user,
            plan_code="1m",
            plan_name="1 месяц",
            amount_rub=990,
            duration_days=30,
            max_devices=3,
            status=SubscriptionPayment.STATUS_PENDING,
            provider_status="awaiting_confirmation",
        )
        Device.objects.create(
            user=self.user,
            name="MacBook Pro",
            display_name="MacBook Pro",
            icon=Device.Icon.LAPTOP,
            ip_address="127.0.0.1",
            last_seen=now - timedelta(days=9),
            status=Device.Status.STALE,
            platform_name="macOS",
            platform="macOS",
            client_name="Outline",
            client="Outline",
        )
        UserActivity.objects.create(
            user=self.user,
            action="profile_updated",
            description="Пользователь обновил профиль.",
            ip_address="127.0.0.1",
            metadata={},
        )

    def test_admin_index_renders_operational_overview_and_workspace_nav(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обзор")
        self.assertContains(response, "Support")
        self.assertContains(response, "Пользователи")
        self.assertContains(response, "Платежи")
        self.assertContains(response, "Подписки")
        self.assertContains(response, "Устройства")
        self.assertContains(response, "Очередь внимания")
        self.assertContains(response, "Быстрые действия")
        self.assertContains(response, "Последние ответы поддержки")
        self.assertContains(response, "Последние платежи")
        self.assertContains(
            response,
            reverse("admin:subscription_subscription_changelist") + "?timeline=ending_soon",
        )
        self.assertContains(
            response,
            reverse("admin:auth_user_changelist") + "?telegram_state=unlinked",
        )
        self.assertContains(
            response,
            reverse("admin:devices_device_changelist") + "?attention_state=needs_review",
        )
        self.assertNotContains(response, "Финансы")
        self.assertNotContains(response, "Проблемы")

    def test_support_workspace_sidebar_is_filtered_to_support_models(self):
        response = self.client.get(reverse("admin:support_supportconversation_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Support")
        self.assertContains(response, "Диалоги поддержки")
        self.assertNotContains(response, "Платежи подписки")
        self.assertNotContains(response, "Привязки Telegram")
