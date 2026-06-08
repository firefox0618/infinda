from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.devices.models import Device
from apps.provisioning.models import ProvisionedDeviceAccess, ProvisioningOperation
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
            public_token="access-public-token",
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

    def test_access_state_includes_provisioning_failures(self):
        subscription = self.create_subscription(
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
        )
        route = subscription.routes.select_related("connection_route__server").first().connection_route
        ProvisioningOperation.objects.create(
            user=self.user,
            subscription=subscription,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.SYNC_SUBSCRIPTION_ACCESS,
            trigger=ProvisioningOperation.Trigger.MANUAL_SYNC,
            status=ProvisioningOperation.Status.FAILED,
            error_code="SERVER_UNAVAILABLE",
            error_message="Server is not available.",
        )

        payload = build_user_access_state(user=self.user)

        self.assertEqual(payload["provisioning_issue_count"], 1)
        self.assertEqual(payload["last_provisioning_error_codes"], ["SERVER_UNAVAILABLE"])
        self.assertEqual(payload["active_provisioned_binding_count"], 0)
        self.assertEqual(payload["error_provisioned_binding_count"], 0)
        self.assertEqual(payload["unhealthy_provisioning_server_count"], 0)
        self.assertEqual(payload["degraded_provisioning_server_count"], 0)

    def test_access_state_includes_provisioned_binding_counts(self):
        subscription = self.create_subscription(
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
        )
        route = subscription.routes.select_related("connection_route__server").first().connection_route
        device = Device.objects.create(
            user=self.user,
            name="Bound device",
            display_name="Bound device",
            icon=Device.Icon.DESKTOP,
            ip_address="127.0.0.2",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="Linux",
            platform="Linux",
            client_name="Desktop",
            client="Desktop",
        )
        ProvisionedDeviceAccess.objects.create(
            user=self.user,
            subscription=subscription,
            device=device,
            route=route,
            server=route.server,
            status=ProvisionedDeviceAccess.Status.ACTIVE,
            external_client_uuid="bound-uuid",
            external_client_email="bound@example.local",
        )
        ProvisionedDeviceAccess.objects.create(
            user=self.user,
            subscription=subscription,
            device=device,
            route=self.routes[1],
            server=self.routes[1].server,
            status=ProvisionedDeviceAccess.Status.ERROR,
            external_client_uuid="error-uuid",
            external_client_email="error@example.local",
            last_error_code="XUI_LOGIN_FAILED",
        )

        payload = build_user_access_state(user=self.user)

        self.assertEqual(payload["active_provisioned_binding_count"], 1)
        self.assertEqual(payload["error_provisioned_binding_count"], 1)

    def test_access_state_includes_unhealthy_server_counts(self):
        self.create_subscription(ends_at=timezone.localdate() + timedelta(days=30), max_devices=3)
        self.routes[0].server.status = Server.Status.OFFLINE
        self.routes[0].server.save(update_fields=["status", "updated_at"])
        self.routes[1].server.status = Server.Status.DEGRADED
        self.routes[1].server.save(update_fields=["status", "updated_at"])

        payload = build_user_access_state(user=self.user)

        self.assertEqual(payload["unhealthy_provisioning_server_count"], 1)
        self.assertEqual(payload["degraded_provisioning_server_count"], 1)


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

    def test_post_access_sync_requires_subscription(self):
        response = self.client.post("/api/access/sync/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "NO_SUBSCRIPTION")

    def test_post_access_sync_schedules_operations(self):
        routes = ensure_default_route_catalog()
        subscription = Subscription.objects.create(
            user=self.user,
            plan_name="3 месяца",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            public_token="access-sync-token",
            main_url="https://infinda.com/sub/access-sync-token",
        )
        for index, route in enumerate(routes[:2], start=1):
            SubscriptionRoute.objects.create(
                subscription=subscription,
                code=route.code,
                label=route.location.name,
                url=route.endpoint_url,
                position=index,
                connection_route=route,
            )

        response = self.client.post("/api/access/sync/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scheduled_operation_count"], 2)
        self.assertEqual(response.data["failed_operation_count"], 0)
