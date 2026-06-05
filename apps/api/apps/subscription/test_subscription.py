import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Subscription, SubscriptionPayment, SubscriptionRoute
from .services import (
    create_trial_subscription,
    extend_subscription_by_days,
    mark_subscription_payment_canceled,
    mark_subscription_payment_failed,
    mark_subscription_payment_paid,
    remove_user_subscription,
)


User = get_user_model()


class SubscriptionApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="subscription-user",
            email="subscription@example.com",
            password="subscription-pass-123",
        )
        self.other_user = User.objects.create_user(
            username="subscription-other",
            email="subscription-other@example.com",
            password="subscription-pass-123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="12 месяцев (безлимит)",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=365),
            max_devices=10,
            main_url="https://infinda.com/sub/main-abc123",
        )
        SubscriptionRoute.objects.bulk_create(
            [
                SubscriptionRoute(
                    subscription=self.subscription,
                    code="ru",
                    label="Россия",
                    url="https://infinda.com/sub/ru-abc123",
                    position=1,
                ),
                SubscriptionRoute(
                    subscription=self.subscription,
                    code="de",
                    label="Германия",
                    url="https://infinda.com/sub/de-abc123",
                    position=2,
                ),
            ]
        )
        Subscription.objects.create(
            user=self.other_user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            main_url="https://infinda.com/sub/other-xyz",
        )

    def test_get_subscription_returns_current_user_data(self):
        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {
                "status",
                "is_trial",
                "plan_name",
                "main_link",
                "active_until",
                "remaining_days",
                "max_devices",
                "countries",
            },
        )
        self.assertEqual(response.data["status"], "active")
        self.assertFalse(response.data["is_trial"])
        self.assertEqual(response.data["plan_name"], "12 месяцев (безлимит)")
        self.assertEqual(response.data["main_link"], "https://infinda.com/sub/main-abc123")
        self.assertEqual(response.data["max_devices"], 10)
        self.assertEqual(len(response.data["countries"]), 2)
        self.assertEqual(response.data["countries"][0]["code"], "ru")

    def test_get_subscription_returns_none_state_without_subscription(self):
        self.subscription.delete()

        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "none"})

    def test_get_subscription_returns_expired_state(self):
        self.subscription.ends_at = timezone.localdate() - timedelta(days=1)
        self.subscription.save(update_fields=["ends_at"])

        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "expired")
        self.assertEqual(response.data["remaining_days"], 0)

    def test_create_trial_subscription_creates_default_routes(self):
        trial_user = User.objects.create_user(
            username="trial-user",
            email="trial@example.com",
            password="trial-pass-123",
        )

        subscription = create_trial_subscription(user=trial_user)

        self.assertEqual(subscription.plan_name, "Триал 3 дня")
        self.assertEqual(subscription.remaining_days, 3)
        self.assertEqual(subscription.max_devices, 3)
        self.assertEqual(subscription.routes.count(), 3)
        self.assertEqual(subscription.routes.first().code, "nl")

    def test_get_subscription_plans_returns_catalog(self):
        response = self.client.get("/api/subscription/plans/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["code"], "1m")
        self.assertEqual(response.data[-1]["code"], "12m")

    def test_extend_subscription_by_days_updates_end_date(self):
        previous_ends_at = self.subscription.ends_at

        extend_subscription_by_days(subscription=self.subscription, days=30)

        self.subscription.refresh_from_db()
        self.assertEqual(
            self.subscription.ends_at,
            previous_ends_at + timedelta(days=30),
        )

    def test_remove_user_subscription_deletes_record(self):
        remove_user_subscription(user=self.user)

        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
    )
    def test_checkout_subscription_creates_platega_payment(self):
        buyer = User.objects.create_user(
            username="checkout-user",
            email="checkout@example.com",
            password="checkout-pass-123",
        )
        buyer_token = Token.objects.create(user=buyer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {buyer_token.key}")

        with patch(
            "apps.subscription.services.PlategaClient.create_payment",
            return_value=SimpleNamespace(
                transaction_id="plat-100",
                checkout_url="https://pay.platega.example/plat-100",
                status="PENDING",
                raw={"transactionId": "plat-100", "redirect": "https://pay.platega.example/plat-100"},
            ),
        ):
            response = self.client.post(
                "/api/subscription/checkout/",
                {"plan_code": "3m"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["plan_code"], "3m")
        self.assertEqual(response.data["provider"], "platega")
        self.assertEqual(response.data["payment_method"], "sbp")
        payment = SubscriptionPayment.objects.get(pk=response.data["payment_id"])
        self.assertEqual(payment.external_payment_id, "plat-100")
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PENDING)

    def test_mark_subscription_payment_paid_activates_subscription(self):
        buyer = User.objects.create_user(
            username="manual-payment-user",
            email="manual-payment@example.com",
            password="manual-pass-123",
        )
        payment = SubscriptionPayment.objects.create(
            user=buyer,
            plan_code="3m",
            plan_name="3 месяца",
            amount_rub=399,
            duration_days=90,
            max_devices=4,
            provider=SubscriptionPayment.PROVIDER_PLATEGA,
            payment_method="sbp",
            status=SubscriptionPayment.STATUS_PENDING,
        )

        mark_subscription_payment_paid(payment=payment)

        payment.refresh_from_db()
        subscription = Subscription.objects.get(user=buyer)
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.provider_status, "CONFIRMED")
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(subscription.plan_name, "3 месяца")
        self.assertEqual(subscription.max_devices, 4)

    def test_mark_subscription_payment_canceled_updates_status(self):
        payment = SubscriptionPayment.objects.create(
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

        mark_subscription_payment_canceled(payment=payment)

        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_CANCELED)

    def test_mark_subscription_payment_failed_updates_status(self):
        payment = SubscriptionPayment.objects.create(
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

        mark_subscription_payment_failed(payment=payment)

        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_FAILED)

    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
        PLATEGA_WEBHOOK_SECRET="webhook-secret",
    )
    def test_platega_webhook_confirms_payment_and_activates_subscription(self):
        buyer = User.objects.create_user(
            username="webhook-user",
            email="webhook@example.com",
            password="webhook-pass-123",
        )
        payment = SubscriptionPayment.objects.create(
            user=buyer,
            plan_code="6m",
            plan_name="6 месяцев",
            amount_rub=749,
            duration_days=180,
            max_devices=5,
            provider="platega",
            payment_method="sbp",
            status=SubscriptionPayment.STATUS_PENDING,
            external_payment_id="plat-200",
            checkout_url="https://pay.platega.example/plat-200",
        )
        body = {
            "id": "plat-200",
            "status": "CONFIRMED",
            "paymentMethod": 2,
            "payload": json.dumps(
                {
                    "type": "subscription",
                    "payment_id": payment.id,
                    "user_id": buyer.id,
                    "plan_code": "6m",
                }
            ),
        }

        response = self.client.post(
            "/api/subscription/webhooks/platega/webhook-secret/",
            data=json.dumps(body),
            content_type="application/json",
            HTTP_X_MERCHANTID="merchant-1",
            HTTP_X_SECRET="secret-1",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.provider_status, "CONFIRMED")
        subscription = Subscription.objects.get(user=buyer)
        self.assertEqual(subscription.plan_name, "6 месяцев")
        self.assertEqual(subscription.max_devices, 5)

    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
        PLATEGA_WEBHOOK_SECRET="webhook-secret",
    )
    def test_platega_webhook_is_idempotent_for_confirmed_payment(self):
        buyer = User.objects.create_user(
            username="duplicate-user",
            email="duplicate@example.com",
            password="duplicate-pass-123",
        )
        payment = SubscriptionPayment.objects.create(
            user=buyer,
            plan_code="1m",
            plan_name="1 месяц",
            amount_rub=149,
            duration_days=30,
            max_devices=3,
            provider="platega",
            payment_method="sbp",
            status=SubscriptionPayment.STATUS_PENDING,
            external_payment_id="plat-300",
            checkout_url="https://pay.platega.example/plat-300",
        )
        body = {
            "id": "plat-300",
            "status": "CONFIRMED",
            "paymentMethod": 2,
            "payload": json.dumps(
                {
                    "type": "subscription",
                    "payment_id": payment.id,
                    "user_id": buyer.id,
                    "plan_code": "1m",
                }
            ),
        }

        first_response = self.client.post(
            "/api/subscription/webhooks/platega/webhook-secret/",
            data=json.dumps(body),
            content_type="application/json",
            HTTP_X_MERCHANTID="merchant-1",
            HTTP_X_SECRET="secret-1",
        )
        first_subscription = Subscription.objects.get(user=buyer)
        first_ends_at = first_subscription.ends_at

        second_response = self.client.post(
            "/api/subscription/webhooks/platega/webhook-secret/",
            data=json.dumps(body),
            content_type="application/json",
            HTTP_X_MERCHANTID="merchant-1",
            HTTP_X_SECRET="secret-1",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        first_subscription.refresh_from_db()
        self.assertEqual(first_subscription.ends_at, first_ends_at)

    def test_platega_webhook_rejects_invalid_secret(self):
        response = self.client.post(
            "/api/subscription/webhooks/platega/wrong-secret/",
            data=json.dumps({"id": "plat-1", "status": "CONFIRMED", "paymentMethod": 2}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
