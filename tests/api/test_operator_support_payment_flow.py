from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from types import SimpleNamespace
from unittest.mock import patch


User = get_user_model()


class OperatorSupportPaymentFlowIntegrationTests(APITestCase):
    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
        PLATEGA_WEBHOOK_SECRET="webhook-secret",
    )
    @patch(
        "apps.subscription.services.PlategaClient.create_payment",
        return_value=SimpleNamespace(
            transaction_id="plat-operator-flow-100",
            checkout_url="https://pay.platega.example/plat-operator-flow-100",
            status="PENDING",
            raw={
                "transactionId": "plat-operator-flow-100",
                "redirect": "https://pay.platega.example/plat-operator-flow-100",
                "status": "PENDING",
            },
        ),
    )
    def test_operator_can_close_support_ticket_and_activate_pending_payment(self, mocked_create_payment):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Operator Flow User",
                "email": "operator-flow@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="operator-flow@example.com")

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "operator-flow@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login_response.data['token']}")

        support_message_response = self.client.post(
            "/api/support/messages/",
            {"text": "Нужна помощь с оплатой."},
            format="multipart",
        )
        self.assertEqual(support_message_response.status_code, status.HTTP_201_CREATED)
        conversation_id = support_message_response.data["id"]

        checkout_response = self.client.post(
            "/api/subscription/checkout/",
            {"plan_code": "3m"},
            format="json",
        )
        self.assertEqual(checkout_response.status_code, status.HTTP_200_OK)
        payment_id = checkout_response.data["payment_id"]

        admin_user = User.objects.create_superuser(
            username="operator-flow-admin",
            email="operator-flow-admin@example.com",
            password="strong-pass-123",
            first_name="Support",
            last_name="Operator",
        )
        admin_token = Token.objects.create(user=admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {admin_token.key}")

        support_list_response = self.client.get("/api/support/admin/conversations/?assigned_to=unassigned")
        self.assertEqual(support_list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(support_list_response.data), 1)
        self.assertEqual(support_list_response.data[0]["id"], conversation_id)
        self.assertEqual(support_list_response.data[0]["user_email"], user.email)

        assign_response = self.client.post(
            f"/api/support/admin/conversations/{conversation_id}/assign/",
            {"admin_user_id": admin_user.id},
            format="json",
        )
        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        self.assertEqual(assign_response.data["assigned_admin_id"], admin_user.id)

        reply_response = self.client.post(
            f"/api/support/admin/conversations/{conversation_id}/reply/",
            {
                "text": "Платеж проверен, активируем подписку и закрываем тикет.",
                "close_after_reply": True,
            },
            format="multipart",
        )
        self.assertEqual(reply_response.status_code, status.HTTP_200_OK)
        self.assertEqual(reply_response.data["status"], "closed")
        self.assertEqual(reply_response.data["assigned_admin_name"], "Support Operator")

        payments_response = self.client.get("/api/subscription/admin/payments/?status=pending")
        self.assertEqual(payments_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(payments_response.data), 1)
        self.assertEqual(payments_response.data[0]["id"], payment_id)

        mark_paid_response = self.client.post(
            f"/api/subscription/admin/payments/{payment_id}/status/",
            {"status": "paid"},
            format="json",
        )
        self.assertEqual(mark_paid_response.status_code, status.HTTP_200_OK)
        self.assertEqual(mark_paid_response.data["status"], "paid")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login_response.data['token']}")

        support_state_response = self.client.get("/api/support/conversation/")
        subscription_state_response = self.client.get("/api/subscription/")

        self.assertEqual(support_state_response.status_code, status.HTTP_200_OK)
        self.assertEqual(support_state_response.data["status"], "closed")
        self.assertEqual(support_state_response.data["assigned_admin_name"], "Support Operator")
        self.assertEqual(len(support_state_response.data["messages"]), 3)

        self.assertEqual(subscription_state_response.status_code, status.HTTP_200_OK)
        self.assertEqual(subscription_state_response.data["status"], "active")
        self.assertEqual(subscription_state_response.data["plan_name"], "3 месяца")
        self.assertFalse(subscription_state_response.data["is_trial"])
