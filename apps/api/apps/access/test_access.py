from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.devices.models import Device
from apps.routing.services import ensure_default_route_catalog
from apps.servers.models import Server
from apps.subscription.models import Subscription, SubscriptionPayment, SubscriptionRoute

from .services import (
    ACCESS_STATUS_ACTIVE,
    ACCESS_STATUS_DEVICE_LIMIT_EXCEEDED,
    ACCESS_STATUS_EXPIRED,
    ACCESS_STATUS_PENDING_PAYMENT,
    ACCESS_STATUS_RESTRICTED,
    ACCESS_STATUS_SERVER_UNAVAILABLE,
    build_user_access_state,
)


User = get_user_model()


class AccessStateServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="access-user",
            email="access@example.com",
            password="access-pass-123",
        )
        self.routes = ensure_default_route_catalog()

    def create_subscription(self, *, ends_at, max_devices=3):
        subscription = Subscription.objects.create(
            user=self.user,
            plan_name="3 месяца",
            starts_at=timezone.localdate(),
            ends_at=ends_at,
            max_devices=max_devices,
            main_url="https://infinda.com/sub/main-access",
        )
        for index, route in enumerate(self.routes, start=1):
            SubscriptionRoute.objects.create(
                subscription=subscription,
                code=route.code,
                label=route.location.name,
                url=route.endpoint_url,
                position=index,
                connection_route=route,
            )
        return subscription

    def create_device(self, name: str):
        Device.objects.create(
            user=self.user,
            name=name,
            display_name=name,
            icon=Device.Icon.DESKTOP,
            ip_address="127.0.0.1",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="Linux",
            platform="Linux",
            client_name="Desktop",
            client="Desktop",
        )

    def test_access_state_returns_restricted_without_subscription(self):
        payload = build_user_access_state(user=self.user)
        self.assertEqual(payload["status"], ACCESS_STATUS_RESTRICTED)
        self.assertEqual(payload["reason"], "no_subscription")

    def test_access_state_returns_expired(self):
        self.create_subscription(ends_at=timezone.localdate() - timedelta(days=1))
        payload = build_user_access_state(user=self.user)
        self.assertEqual(payload["status"], ACCESS_STATUS_EXPIRED)

    def test_access_state_returns_pending_payment(self):
        SubscriptionPayment.objects.create(
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
        payload = build_user_access_state(user=self.user)
        self.assertEqual(payload["status"], ACCESS_STATUS_PENDING_PAYMENT)

    def test_access_state_returns_device_limit_exceeded(self):
        self.create_subscription(ends_at=timezone.localdate() + timedelta(days=30), max_devices=1)
        self.create_device("Device 1")
        self.create_device("Device 2")
        payload = build_user_access_state(user=self.user)
        self.assertEqual(payload["status"], ACCESS_STATUS_DEVICE_LIMIT_EXCEEDED)

    def test_access_state_returns_server_unavailable(self):
        self.create_subscription(ends_at=timezone.localdate() + timedelta(days=30), max_devices=3)
        Server.objects.update(status=Server.Status.OFFLINE)
        payload = build_user_access_state(user=self.user)
        self.assertEqual(payload["status"], ACCESS_STATUS_SERVER_UNAVAILABLE)

    def test_access_state_returns_active(self):
        self.create_subscription(ends_at=timezone.localdate() + timedelta(days=30), max_devices=3)
        self.create_device("Device 1")
        payload = build_user_access_state(user=self.user)
        self.assertEqual(payload["status"], ACCESS_STATUS_ACTIVE)


class AccessStateApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="access-api-user",
            email="access-api@example.com",
            password="access-pass-123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_current_access_state(self):
        response = self.client.get("/api/access/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], ACCESS_STATUS_RESTRICTED)
