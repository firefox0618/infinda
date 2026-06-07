from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.support.models import SupportConversation
from apps.support.services import (
    close_support_conversation,
    create_support_message_from_admin,
    create_support_message_from_telegram,
)


User = get_user_model()


class TelegramSupportFlowIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="telegram-integration-user",
            email="telegram-integration@example.com",
            password="strong-pass-123",
        )
        self.admin_user = User.objects.create_superuser(
            username="telegram-integration-admin",
            email="telegram-admin@example.com",
            password="strong-pass-123",
            first_name="Support",
            last_name="Agent",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    @patch("apps.support.services.send_telegram_message")
    @patch("apps.support.services.notify_support_team_about_ticket")
    def test_telegram_link_support_reply_and_close_flow(
        self,
        notify_support_team_about_ticket,
        send_telegram_message,
    ):
        create_link_response = self.client.post("/api/telegram/link/")

        self.assertEqual(create_link_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", create_link_response.data)
        link_token = create_link_response.data["token"]

        confirm_link_response = self.client.post(
            "/api/telegram/link/confirm/",
            {
                "token": link_token,
                "telegram_user_id": 123456789,
                "telegram_username": "telegram_client",
                "telegram_full_name": "Telegram Client",
            },
            format="json",
        )

        self.assertEqual(confirm_link_response.status_code, status.HTTP_200_OK)
        self.assertTrue(confirm_link_response.data["ok"])

        conversation = create_support_message_from_telegram(
            user=self.user,
            sender_display_name="Telegram Client (@telegram_client)",
            text="Не работает продление подписки.",
            attachments=[],
            telegram_user_id=123456789,
        )

        notify_support_team_about_ticket.assert_called_once()
        self.assertIn("Новый тикет", notify_support_team_about_ticket.call_args.kwargs["text"])
        self.assertIn("Telegram", notify_support_team_about_ticket.call_args.kwargs["text"])

        conversation.refresh_from_db()
        self.assertEqual(conversation.status, SupportConversation.Status.NEW)
        self.assertEqual(conversation.messages.count(), 1)
        first_message = conversation.messages.first()
        self.assertEqual(first_message.source, "telegram_support_bot")

        create_support_message_from_admin(
            admin_user=self.admin_user,
            conversation=conversation,
            text="Проверили платежный контур. Попробуйте снова через минуту.",
        )

        conversation.refresh_from_db()
        self.assertEqual(conversation.status, SupportConversation.Status.IN_PROGRESS)
        self.assertEqual(conversation.assigned_admin, self.admin_user)
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(send_telegram_message.call_count, 1)
        self.assertEqual(send_telegram_message.call_args.kwargs["chat_id"], 123456789)
        self.assertIn("Ответ по тикету", send_telegram_message.call_args.kwargs["text"])
        self.assertIn("Support Agent", send_telegram_message.call_args.kwargs["text"])

        close_support_conversation(
            conversation=conversation,
            closed_by=self.admin_user,
        )

        conversation.refresh_from_db()
        self.assertEqual(conversation.status, SupportConversation.Status.CLOSED)
        self.assertIsNotNone(conversation.closed_at)
        self.assertEqual(conversation.messages.count(), 3)
        self.assertEqual(send_telegram_message.call_count, 2)
        self.assertIn("закрыт", send_telegram_message.call_args.kwargs["text"])

        support_response = self.client.get("/api/support/conversation/")
        self.assertEqual(support_response.status_code, status.HTTP_200_OK)
        self.assertEqual(support_response.data["status"], "closed")
        self.assertEqual(support_response.data["assigned_admin_name"], "Support Agent")
        self.assertEqual(len(support_response.data["messages"]), 3)
        self.assertEqual(
            support_response.data["messages"][0]["source"],
            "telegram_support_bot",
        )
        self.assertEqual(
            support_response.data["messages"][1]["sender_display_name"],
            "Support Agent",
        )
