from datetime import timedelta
from unittest.mock import MagicMock, patch

import httpx
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.devices.models import Device
from apps.routing.services import ensure_default_route_catalog
from apps.servers.models import Server
from apps.subscription.models import Subscription, SubscriptionRoute

from .models import ProvisionedDeviceAccess, ProvisioningOperation, ServerProvisioningProfile
from .services import (
    build_user_provisioning_summary,
    ensure_provisioned_device_access,
    execute_provisioning_operation,
    refresh_enabled_provisioning_servers,
    refresh_server_provisioning_health,
    schedule_device_revoke,
    schedule_subscription_sync,
)


User = get_user_model()


class ProvisioningServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="provision-user",
            email="provision@example.com",
            password="provision-pass-123",
        )
        self.device = Device.objects.create(
            user=self.user,
            name="Provision Device",
            display_name="Provision Device",
            icon=Device.Icon.DESKTOP,
            ip_address="10.10.10.10",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="Linux",
            platform="Linux",
            client_name="Happ",
            client="Happ",
        )
        self.second_device = Device.objects.create(
            user=self.user,
            name="Second Device",
            display_name="Second Device",
            icon=Device.Icon.MOBILE,
            ip_address="10.10.10.11",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="iOS",
            platform="iOS",
            client_name="Happ",
            client="Happ",
        )
        self.routes = ensure_default_route_catalog()
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="3 месяца",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=90),
            max_devices=3,
            public_token="provision-public-token",
            main_url="https://infinda.com/sub/provision-public-token",
        )
        for index, route in enumerate(self.routes[:2], start=1):
            SubscriptionRoute.objects.create(
                subscription=self.subscription,
                code=route.code,
                label=route.location.name,
                url=route.endpoint_url,
                position=index,
                connection_route=route,
            )

    def test_schedule_subscription_sync_creates_bindings_for_all_active_devices(self):
        operations = schedule_subscription_sync(
            subscription=self.subscription,
            trigger=ProvisioningOperation.Trigger.SUBSCRIPTION_ACTIVATED,
        )

        self.assertEqual(len(operations), 2)
        self.assertTrue(
            all(item.status == ProvisioningOperation.Status.SUCCEEDED for item in operations)
        )
        self.assertEqual(ServerProvisioningProfile.objects.count(), 2)
        self.assertEqual(ProvisionedDeviceAccess.objects.count(), 4)
        self.assertEqual(
            ProvisionedDeviceAccess.objects.filter(status=ProvisionedDeviceAccess.Status.ACTIVE).count(),
            4,
        )

    def test_refresh_server_provisioning_health_marks_mock_server_active(self):
        server = self.routes[0].server

        result = refresh_server_provisioning_health(server=server)

        server.refresh_from_db()
        self.assertEqual(result["status"], Server.Status.ACTIVE)
        self.assertEqual(server.status, Server.Status.ACTIVE)
        self.assertEqual(server.status_snapshots.count(), 1)

    def test_schedule_device_revoke_revokes_existing_bindings(self):
        schedule_subscription_sync(
            subscription=self.subscription,
            trigger=ProvisioningOperation.Trigger.SUBSCRIPTION_ACTIVATED,
        )

        operations = schedule_device_revoke(
            subscription=self.subscription,
            device=self.device,
            reason="lost-device",
        )

        self.assertEqual(len(operations), 2)
        self.assertTrue(
            all(item.status == ProvisioningOperation.Status.SUCCEEDED for item in operations)
        )
        self.assertEqual(
            ProvisionedDeviceAccess.objects.filter(
                device=self.device,
                status=ProvisionedDeviceAccess.Status.REVOKED,
            ).count(),
            2,
        )
        self.assertEqual(
            ProvisionedDeviceAccess.objects.filter(
                device=self.second_device,
                status=ProvisionedDeviceAccess.Status.ACTIVE,
            ).count(),
            2,
        )

    def test_schedule_device_revoke_creates_failed_operations_for_offline_server(self):
        first_route = self.routes[0]
        first_route.server.status = Server.Status.OFFLINE
        first_route.server.save(update_fields=["status", "updated_at"])

        schedule_subscription_sync(
            subscription=self.subscription,
            trigger=ProvisioningOperation.Trigger.SUBSCRIPTION_ACTIVATED,
        )
        operations = schedule_device_revoke(
            subscription=self.subscription,
            device=self.device,
            reason="lost-device",
        )

        self.assertEqual(len(operations), 2)
        self.assertEqual(operations[0].status, ProvisioningOperation.Status.FAILED)
        self.assertEqual(operations[0].error_code, "SERVER_UNAVAILABLE")
        self.assertEqual(operations[1].status, ProvisioningOperation.Status.SUCCEEDED)

    def test_build_user_provisioning_summary_reports_failed_operations_and_binding_errors(self):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        binding = ensure_provisioned_device_access(
            subscription=self.subscription,
            device=self.device,
            route=route,
        )
        binding.status = ProvisionedDeviceAccess.Status.ERROR
        binding.last_error_code = "SERVER_UNAVAILABLE"
        binding.save(update_fields=["status", "last_error_code", "updated_at"])
        ProvisioningOperation.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=self.device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REPAIR_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
            status=ProvisioningOperation.Status.FAILED,
            error_code="SERVER_UNAVAILABLE",
            error_message="Server is not available.",
        )

        summary = build_user_provisioning_summary(user=self.user)

        self.assertEqual(summary["recent_operation_count"], 1)
        self.assertEqual(summary["failed_operation_count"], 1)
        self.assertEqual(summary["error_binding_count"], 1)
        self.assertEqual(summary["unhealthy_server_count"], 0)
        self.assertIn("SERVER_UNAVAILABLE", summary["last_error_codes"])

    @patch("apps.provisioning.adapters.httpx.Client")
    def test_execute_provisioning_operation_creates_xui_binding(self, client_class):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        ServerProvisioningProfile.objects.create(
            server=route.server,
            adapter=ServerProvisioningProfile.Adapter.XUI,
            panel_base_url="https://xui.example",
            panel_username="admin",
            panel_password="secret",
            default_inbound_id=7,
        )
        operation = ProvisioningOperation.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=self.device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REPAIR_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
        )

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        login_response = MagicMock(status_code=200)
        inbound_response = MagicMock()
        inbound_response.json.return_value = {
            "success": True,
            "obj": [
                {
                    "id": 7,
                    "protocol": "vless",
                    "port": 443,
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "settings": {
                                "publicKey": "pubkey",
                                "fingerprint": "chrome",
                                "serverNames": ["example.org"],
                                "shortIds": ["abcd"],
                            }
                        },
                    },
                },
            ],
        }
        add_response = MagicMock()
        add_response.json.return_value = {"success": True}
        client.get.return_value = inbound_response
        client.post.side_effect = [login_response, add_response]
        client_class.return_value = client

        execute_provisioning_operation(operation=operation)

        operation.refresh_from_db()
        binding = ProvisionedDeviceAccess.objects.get(device=self.device, route=route)
        self.assertEqual(operation.status, ProvisioningOperation.Status.SUCCEEDED)
        self.assertEqual(binding.adapter, ServerProvisioningProfile.Adapter.XUI)
        self.assertEqual(binding.inbound_id, 7)
        self.assertTrue(binding.connection_url.startswith("vless://"))
        self.assertEqual(binding.status, ProvisionedDeviceAccess.Status.ACTIVE)

    @patch("apps.provisioning.adapters.httpx.Client")
    def test_execute_provisioning_operation_updates_existing_xui_binding(self, client_class):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        ServerProvisioningProfile.objects.create(
            server=route.server,
            adapter=ServerProvisioningProfile.Adapter.XUI,
            panel_base_url="https://xui.example",
            panel_username="admin",
            panel_password="secret",
            default_inbound_id=7,
        )
        binding = ensure_provisioned_device_access(
            subscription=self.subscription,
            device=self.device,
            route=route,
        )
        binding.external_client_uuid = "existing-uuid"
        binding.external_client_email = "existing@example.local"
        binding.save(update_fields=["external_client_uuid", "external_client_email", "updated_at"])
        operation = ProvisioningOperation.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=self.device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REPAIR_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
        )

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        login_response = MagicMock(status_code=200)
        inbound_response = MagicMock()
        inbound_response.json.return_value = {
            "success": True,
            "obj": [{"id": 7, "protocol": "vless", "port": 443}],
        }
        update_response = MagicMock()
        update_response.json.return_value = {"success": True}
        client.get.return_value = inbound_response
        client.post.side_effect = [login_response, update_response]
        client_class.return_value = client

        execute_provisioning_operation(operation=operation)

        operation.refresh_from_db()
        binding.refresh_from_db()
        self.assertEqual(operation.status, ProvisioningOperation.Status.SUCCEEDED)
        self.assertEqual(binding.external_client_uuid, "existing-uuid")
        self.assertEqual(binding.external_client_email, "existing@example.local")

    @patch("apps.provisioning.adapters.httpx.Client")
    def test_execute_provisioning_operation_deletes_xui_binding(self, client_class):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        ServerProvisioningProfile.objects.create(
            server=route.server,
            adapter=ServerProvisioningProfile.Adapter.XUI,
            panel_base_url="https://xui.example",
            panel_username="admin",
            panel_password="secret",
            default_inbound_id=7,
        )
        binding = ensure_provisioned_device_access(
            subscription=self.subscription,
            device=self.device,
            route=route,
        )
        binding.external_client_email = "delete@example.local"
        binding.external_client_uuid = "delete-uuid"
        binding.save(update_fields=["external_client_email", "external_client_uuid", "updated_at"])
        operation = ProvisioningOperation.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=self.device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REVOKE_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.DEVICE_REVOKED,
        )

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        login_response = MagicMock(status_code=200)
        delete_response = MagicMock()
        delete_response.json.return_value = {"success": True}
        client.post.side_effect = [login_response, delete_response]
        client_class.return_value = client

        execute_provisioning_operation(operation=operation)

        operation.refresh_from_db()
        binding.refresh_from_db()
        self.assertEqual(operation.status, ProvisioningOperation.Status.SUCCEEDED)
        self.assertEqual(binding.status, ProvisionedDeviceAccess.Status.REVOKED)

    def test_execute_provisioning_operation_fails_for_incomplete_xui_config(self):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        ServerProvisioningProfile.objects.create(
            server=route.server,
            adapter=ServerProvisioningProfile.Adapter.XUI,
            panel_base_url="",
            panel_username="",
            panel_password="",
        )
        operation = ProvisioningOperation.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=self.device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REPAIR_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
        )

        execute_provisioning_operation(operation=operation)

        operation.refresh_from_db()
        binding = ProvisionedDeviceAccess.objects.get(device=self.device, route=route)
        self.assertEqual(operation.status, ProvisioningOperation.Status.FAILED)
        self.assertEqual(operation.error_code, "XUI_CONFIG_INCOMPLETE")
        self.assertEqual(binding.status, ProvisionedDeviceAccess.Status.ERROR)
        self.assertEqual(route.server.status, Server.Status.OFFLINE)

    @patch("apps.provisioning.adapters.httpx.Client")
    def test_xui_adapter_falls_back_to_clients_add_api(self, client_class):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        ServerProvisioningProfile.objects.create(
            server=route.server,
            adapter=ServerProvisioningProfile.Adapter.XUI,
            panel_base_url="https://xui.example",
            panel_username="admin",
            panel_password="secret",
            default_inbound_id=7,
        )
        operation = ProvisioningOperation.objects.create(
            user=self.user,
            subscription=self.subscription,
            device=self.device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REPAIR_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
        )

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        login_response = MagicMock(status_code=200)
        inbound_response = MagicMock()
        inbound_response.json.return_value = {
            "success": True,
            "obj": [{"id": 7, "protocol": "vless", "port": 443}],
        }
        not_found_error = httpx.HTTPStatusError(
            "not found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )
        add_response = MagicMock()
        add_response.json.return_value = {"success": True}
        add_response.raise_for_status.return_value = None

        failed_add_response = MagicMock()
        failed_add_response.raise_for_status.side_effect = not_found_error
        client.get.return_value = inbound_response
        client.post.side_effect = [login_response, failed_add_response, add_response]
        client_class.return_value = client

        execute_provisioning_operation(operation=operation)

        operation.refresh_from_db()
        self.assertEqual(operation.status, ProvisioningOperation.Status.SUCCEEDED)

    def test_refresh_enabled_provisioning_servers_returns_enabled_profiles(self):
        route = self.subscription.routes.select_related("connection_route__server").first().connection_route
        ServerProvisioningProfile.objects.update_or_create(
            server=route.server,
            defaults={"adapter": ServerProvisioningProfile.Adapter.MOCK, "is_enabled": True},
        )

        checks = refresh_enabled_provisioning_servers()

        self.assertGreaterEqual(len(checks), 1)
        self.assertEqual(checks[0]["status"], Server.Status.ACTIVE)

    def test_check_provisioning_servers_command_runs(self):
        call_command("check_provisioning_servers")
