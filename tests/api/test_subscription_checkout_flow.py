import json
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.subscription.models import SubscriptionPayment


User = get_user_model()


class SubscriptionCheckoutFlowIntegrationTests(APITestCase):
    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
        PLATEGA_WEBHOOK_SECRET="webhook-secret",
    )
    @patch(
        "apps.subscription.services.PlategaClient.create_payment",
        return_value=SimpleNamespace(
            transaction_id="plat-integration-100",
            checkout_url="https://pay.platega.example/plat-integration-100",
            status="PENDING",
            raw={
                "transactionId": "plat-integration-100",
                "redirect": "https://pay.platega.example/plat-integration-100",
                "status": "PENDING",
            },
        ),
    )
    def test_register_checkout_webhook_and_subscription_activation(self, mocked_create_payment):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Checkout Integration",
                "email": "checkout-integration@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        fresh_user = User.objects.get(email="checkout-integration@example.com")
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "checkout-integration@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login_response.data['token']}")

        subscription_before = self.client.get("/api/subscription/")
        self.assertEqual(subscription_before.status_code, status.HTTP_200_OK)
        self.assertEqual(subscription_before.data["status"], "trial")

        checkout_response = self.client.post(
            "/api/subscription/checkout/",
            {"plan_code": "6m"},
            format="json",
        )

        self.assertEqual(checkout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(checkout_response.data["plan_code"], "6m")
        self.assertEqual(checkout_response.data["provider"], "platega")
        self.assertEqual(checkout_response.data["status"], "pending")
        mocked_create_payment.assert_called_once()

        payment = SubscriptionPayment.objects.get(pk=checkout_response.data["payment_id"])
        self.assertEqual(payment.user, fresh_user)
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PENDING)
        self.assertEqual(payment.external_payment_id, "plat-integration-100")

        webhook_body = {
            "id": "plat-integration-100",
            "status": "CONFIRMED",
            "paymentMethod": 2,
            "payload": json.dumps(
                {
                    "type": "subscription",
                    "payment_id": payment.id,
                    "user_id": fresh_user.id,
                    "plan_code": "6m",
                }
            ),
        }

        webhook_response = self.client.post(
            "/api/subscription/webhooks/platega/webhook-secret/",
            data=json.dumps(webhook_body),
            content_type="application/json",
            HTTP_X_MERCHANTID="merchant-1",
            HTTP_X_SECRET="secret-1",
        )

        self.assertEqual(webhook_response.status_code, status.HTTP_200_OK)
        self.assertTrue(webhook_response.data["ok"])

        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.provider_status, "CONFIRMED")
        self.assertIsNotNone(payment.paid_at)

        subscription_after = self.client.get("/api/subscription/")
        self.assertEqual(subscription_after.status_code, status.HTTP_200_OK)
        self.assertEqual(subscription_after.data["status"], "active")
        self.assertEqual(subscription_after.data["plan_name"], "6 месяцев")
        self.assertFalse(subscription_after.data["is_trial"])
        self.assertEqual(subscription_after.data["max_devices"], 5)
        self.assertEqual(len(subscription_after.data["countries"]), 4)
