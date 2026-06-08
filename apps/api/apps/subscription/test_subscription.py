import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.devices.models import Device
from apps.notifications.models import Notification
from apps.provisioning.models import ProvisionedDeviceAccess, ProvisioningOperation
from apps.routing.services import ensure_default_route_catalog, get_connection_route_by_code

from .models import Subscription, SubscriptionHistoryEvent, SubscriptionPayment, SubscriptionRoute
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
        ensure_default_route_catalog()
        self.route_ru = get_connection_route_by_code(code="ru")
        self.route_de = get_connection_route_by_code(code="de")

        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="12 месяцев (безлимит)",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=365),
            max_devices=10,
            public_token="public-token-123",
            main_url="https://infinda.com/sub/main-abc123",
        )
        SubscriptionRoute.objects.bulk_create(
            [
                SubscriptionRoute(
                    subscription=self.subscription,
                    code="ru",
                    label="Россия",
                    url=self.route_ru.endpoint_url,
                    position=1,
                    connection_route=self.route_ru,
                ),
                SubscriptionRoute(
                    subscription=self.subscription,
                    code="de",
                    label="Германия",
                    url=self.route_de.endpoint_url,
                    position=2,
                    connection_route=self.route_de,
                ),
            ]
        )
        Subscription.objects.create(
            user=self.other_user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="public-token-456",
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
                "feed_link",
                "happ_link",
                "happ_deep_link",
                "happ_routing_link",
                "client_links",
                "active_until",
                "remaining_days",
                "max_devices",
                "uses_provisioned_access",
                "provisioned_route_count",
                "resolved_device_name",
                "countries",
                "payment_history",
                "subscription_history",
                "pending_payment",
            },
        )
        self.assertEqual(response.data["status"], "active")
        self.assertFalse(response.data["is_trial"])
        self.assertEqual(response.data["plan_name"], "12 месяцев (безлимит)")
        self.assertEqual(response.data["main_link"], "https://infinda.com/sub/main-abc123")
        self.assertEqual(response.data["feed_link"], "http://localhost:3000/sub/public-token-123/feed")
        self.assertEqual(
            response.data["happ_link"],
            "http://localhost:3000/happ/add?sub=http%3A%2F%2Flocalhost%3A3000%2Fsub%2Fpublic-token-123%2Ffeed",
        )
        self.assertEqual(
            response.data["happ_deep_link"],
            "happ://add/http://localhost:3000/sub/public-token-123/feed",
        )
        self.assertEqual(len(response.data["client_links"]), 3)
        self.assertEqual(response.data["max_devices"], 10)
        self.assertFalse(response.data["uses_provisioned_access"])
        self.assertEqual(response.data["provisioned_route_count"], 0)
        self.assertIsNone(response.data["resolved_device_name"])
        self.assertEqual(len(response.data["countries"]), 2)
        self.assertEqual(response.data["countries"][0]["code"], "ru")
        self.assertFalse(response.data["countries"][0]["is_provisioned"])
        self.assertEqual(response.data["payment_history"], [])
        self.assertEqual(response.data["pending_payment"], None)

    def test_get_subscription_returns_provisioned_route_for_current_device_ip(self):
        device = Device.objects.create(
            user=self.user,
            name="MacBook",
            display_name="MacBook",
            icon=Device.Icon.LAPTOP,
            ip_address="203.0.113.10",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="macOS",
            platform="macOS",
            client_name="Happ",
            client="Happ",
        )
        ProvisionedDeviceAccess.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=device,
            route=self.route_ru,
            server=self.route_ru.server,
            status=ProvisionedDeviceAccess.Status.ACTIVE,
            external_client_uuid="route-uuid-1",
            external_client_email="route-1@example.local",
            connection_url="vless://device-route-1",
        )

        response = self.client.get("/api/subscription/", REMOTE_ADDR="203.0.113.10")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["uses_provisioned_access"])
        self.assertEqual(response.data["provisioned_route_count"], 1)
        self.assertEqual(response.data["resolved_device_name"], "MacBook")
        self.assertEqual(response.data["countries"][0]["url"], "vless://device-route-1")
        self.assertTrue(response.data["countries"][0]["is_provisioned"])

    def test_get_subscription_prefers_device_key_over_ip_match(self):
        device = Device.objects.create(
            user=self.user,
            name="Bound laptop",
            display_name="Bound laptop",
            icon=Device.Icon.LAPTOP,
            ip_address="198.51.100.61",
            public_device_key="device-key-123",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="macOS",
            platform="macOS",
            client_name="Happ",
            client="Happ",
        )
        ProvisionedDeviceAccess.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=device,
            route=self.route_ru,
            server=self.route_ru.server,
            status=ProvisionedDeviceAccess.Status.ACTIVE,
            external_client_uuid="route-uuid-2",
            external_client_email="route-2@example.local",
            connection_url="vless://device-key-route",
        )

        response = self.client.get(
            "/api/subscription/",
            REMOTE_ADDR="203.0.113.61",
            HTTP_X_DEVICE_KEY="device-key-123",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["countries"][0]["url"], "vless://device-key-route")
        self.assertEqual(response.data["resolved_device_name"], "Bound laptop")

    def test_get_subscription_returns_none_state_without_subscription(self):
        self.subscription.delete()

        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "none", "pending_payment": None})

    def test_get_subscription_returns_expired_state(self):
        self.subscription.ends_at = timezone.localdate() - timedelta(days=1)
        self.subscription.save(update_fields=["ends_at"])

        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "expired")
        self.assertEqual(response.data["remaining_days"], 0)

    def test_get_subscription_returns_pending_payment_state_without_subscription(self):
        self.subscription.delete()
        pending_payment = SubscriptionPayment.objects.create(
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

        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "pending_payment")
        self.assertEqual(response.data["pending_payment"]["id"], pending_payment.id)

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
        self.assertTrue(subscription.public_token)
        self.assertIn(subscription.public_token, subscription.main_url)
        self.assertEqual(subscription.routes.count(), 3)
        self.assertEqual(subscription.routes.first().code, "nl")
        self.assertEqual(
            ProvisioningOperation.objects.filter(
                user=trial_user,
                subscription=subscription,
                operation_type=ProvisioningOperation.OperationType.SYNC_SUBSCRIPTION_ACCESS,
                trigger=ProvisioningOperation.Trigger.TRIAL_STARTED,
            ).count(),
            3,
        )

    def test_get_subscription_plans_returns_catalog(self):
        response = self.client.get("/api/subscription/plans/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["code"], "1m")
        self.assertEqual(response.data[-1]["code"], "12m")

    def test_get_public_subscription_summary_returns_public_data(self):
        response = self.client.get("/api/subscription/public/public-token-123/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["plan_name"], "12 месяцев (безлимит)")
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["main_link"], "https://infinda.com/sub/main-abc123")
        self.assertEqual(response.data["feed_link"], "http://localhost:3000/sub/public-token-123/feed")
        self.assertEqual(len(response.data["client_links"]), 3)
        self.assertGreaterEqual(len(response.data["install_guides"]), 6)
        self.assertEqual(response.data["install_guides"][0]["code"], "android")
        self.assertEqual(response.data["install_guides"][0]["links"][0]["label"], "Google Play")
        self.assertEqual(len(response.data["countries"]), 2)
        self.assertFalse(response.data["uses_provisioned_access"])

    def test_get_public_subscription_summary_returns_404_for_unknown_token(self):
        response = self.client.get("/api/subscription/public/missing-token/summary/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "NOT_FOUND")

    def test_get_public_subscription_feed_returns_plain_text_urls(self):
        response = self.client.get("/api/subscription/public/public-token-123/feed/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn(self.route_ru.endpoint_url, response.content.decode("utf-8"))
        self.assertIn(self.route_de.endpoint_url, response.content.decode("utf-8"))

    def test_public_subscription_summary_and_feed_use_provisioned_routes_for_known_device_ip(self):
        device = Device.objects.create(
            user=self.user,
            name="iPhone",
            display_name="iPhone",
            icon=Device.Icon.MOBILE,
            ip_address="198.51.100.20",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="iOS",
            platform="iOS",
            client_name="Happ",
            client="Happ",
        )
        ProvisionedDeviceAccess.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=device,
            route=self.route_ru,
            server=self.route_ru.server,
            status=ProvisionedDeviceAccess.Status.ACTIVE,
            external_client_uuid="public-uuid-1",
            external_client_email="public-1@example.local",
            connection_url="vless://public-device-route-1",
        )

        summary_response = self.client.get(
            "/api/subscription/public/public-token-123/summary/",
            REMOTE_ADDR="198.51.100.20",
        )
        feed_response = self.client.get(
            "/api/subscription/public/public-token-123/feed/",
            REMOTE_ADDR="198.51.100.20",
        )

        self.assertEqual(summary_response.status_code, 200)
        self.assertTrue(summary_response.data["uses_provisioned_access"])
        self.assertEqual(summary_response.data["resolved_device_name"], "iPhone")
        self.assertEqual(summary_response.data["countries"][0]["url"], "vless://public-device-route-1")
        self.assertTrue(summary_response.data["countries"][0]["is_provisioned"])
        self.assertIn("vless://public-device-route-1", feed_response.content.decode("utf-8"))

    def test_touch_public_subscription_returns_ok(self):
        response = self.client.post(
            "/api/subscription/public/public-token-123/touch/",
            {
                "device_name": "iPhone device",
                "platform": "iPhone",
                "client": "Happ",
                "icon": "mobile",
            },
            REMOTE_ADDR="198.51.100.45",
            HTTP_X_DEVICE_KEY="touch-key-1",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])
        self.assertTrue(response.data["created"])
        self.assertEqual(response.data["device"]["display_name"], "iPhone device")
        self.assertEqual(response.data["scheduled_operation_count"], 2)
        self.assertEqual(
            Device.objects.get(user=self.user, ip_address="198.51.100.45").public_device_key,
            "touch-key-1",
        )
        self.assertEqual(
            Device.objects.filter(
                user=self.user,
                ip_address="198.51.100.45",
                revoked_at__isnull=True,
            ).count(),
            1,
        )

    def test_touch_public_subscription_updates_existing_device(self):
        device = Device.objects.create(
            user=self.user,
            name="Old device",
            display_name="Old device",
            icon=Device.Icon.DESKTOP,
            ip_address="198.51.100.46",
            last_seen=timezone.now() - timedelta(days=1),
            status=Device.Status.STALE,
            platform_name="Windows",
            platform="Windows",
            client_name="Other",
            client="Other",
        )

        response = self.client.post(
            "/api/subscription/public/public-token-123/touch/",
            {
                "device_name": "Updated device",
                "platform": "macOS",
                "client": "Happ",
                "icon": "laptop",
            },
            REMOTE_ADDR="198.51.100.46",
            HTTP_X_DEVICE_KEY="touch-key-2",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["created"])
        device.refresh_from_db()
        self.assertEqual(device.platform, "macOS")
        self.assertEqual(device.client, "Happ")
        self.assertEqual(device.status, Device.Status.ACTIVE)
        self.assertEqual(device.public_device_key, "touch-key-2")

    def test_touch_public_subscription_rejects_inactive_subscription(self):
        self.subscription.ends_at = timezone.localdate() - timedelta(days=1)
        self.subscription.save(update_fields=["ends_at"])

        response = self.client.post(
            "/api/subscription/public/public-token-123/touch/",
            {
                "device_name": "Inactive device",
            },
            REMOTE_ADDR="198.51.100.47",
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "SUBSCRIPTION_INACTIVE")

    def test_touch_public_subscription_uses_unified_error_contract_for_device_limit(self):
        self.subscription.max_devices = 1
        self.subscription.save(update_fields=["max_devices", "updated_at"])
        Device.objects.create(
            user=self.user,
            name="Existing device",
            display_name="Existing device",
            icon=Device.Icon.DESKTOP,
            ip_address="198.51.100.48",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="Windows",
            platform="Windows",
            client_name="Happ",
            client="Happ",
        )

        response = self.client.post(
            "/api/subscription/public/public-token-123/touch/",
            {"device_name": "New device"},
            REMOTE_ADDR="198.51.100.49",
            HTTP_X_DEVICE_KEY="touch-key-limit",
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "DEVICE_LIMIT_EXCEEDED")
        self.assertIn("max_devices", response.data["error"]["details"])

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
        self.assertTrue(subscription.public_token)
        self.assertIn(subscription.public_token, subscription.main_url)
        self.assertGreaterEqual(
            ProvisioningOperation.objects.filter(
                user=buyer,
                subscription=subscription,
                operation_type=ProvisioningOperation.OperationType.SYNC_SUBSCRIPTION_ACCESS,
                trigger=ProvisioningOperation.Trigger.SUBSCRIPTION_ACTIVATED,
            ).count(),
            4,
        )
        self.assertEqual(buyer.subscription_history_events.count(), 1)

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
        history_event = SubscriptionHistoryEvent.objects.get(payment=payment)
        self.assertEqual(history_event.event_type, SubscriptionHistoryEvent.EVENT_ACTIVATED)
        notification = Notification.objects.get(user=buyer, event_type=Notification.EVENT_PAYMENT_PAID)
        self.assertEqual(notification.payload["payment_id"], payment.id)
        self.assertEqual(notification.payload["plan_name"], "6 месяцев")

    @override_settings(
        PLATEGA_MERCHANT_ID="merchant-1",
        PLATEGA_SECRET_KEY="secret-1",
        PLATEGA_WEBHOOK_SECRET="webhook-secret",
    )
    def test_platega_webhook_cancels_pending_payment(self):
        buyer = User.objects.create_user(
            username="canceled-user",
            email="canceled@example.com",
            password="canceled-pass-123",
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
            external_payment_id="plat-400",
            checkout_url="https://pay.platega.example/plat-400",
        )
        body = {
            "id": "plat-400",
            "status": "CANCELED",
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

        response = self.client.post(
            "/api/subscription/webhooks/platega/webhook-secret/",
            data=json.dumps(body),
            content_type="application/json",
            HTTP_X_MERCHANTID="merchant-1",
            HTTP_X_SECRET="secret-1",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_CANCELED)
        self.assertEqual(payment.provider_status, "CANCELED")
        self.assertFalse(Subscription.objects.filter(user=buyer).exists())
        self.assertFalse(
            Notification.objects.filter(user=buyer, event_type=Notification.EVENT_PAYMENT_PAID).exists()
        )

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
