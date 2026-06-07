from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.activity.models import UserActivity

from .models import Device


User = get_user_model()


class DevicesApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="device-user",
            email="device@example.com",
            password="device-pass-123",
        )
        self.other_user = User.objects.create_user(
            username="device-other",
            email="other@example.com",
            password="device-pass-123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.device = Device.objects.create(
            user=self.user,
            name="Windows PC",
            display_name="Windows PC",
            icon=Device.Icon.DESKTOP,
            ip_address="192.168.1.101",
            last_seen=timezone.now(),
            status=Device.Status.ACTIVE,
            platform_name="Windows 11",
            platform="Windows 11",
            client_name="Chrome 125",
            client="Chrome 125",
        )
        self.other_device = Device.objects.create(
            user=self.other_user,
            name="Other Device",
            display_name="Other Device",
            icon=Device.Icon.MOBILE,
            ip_address="192.168.1.102",
            last_seen=timezone.now() - timedelta(days=45),
            status=Device.Status.STALE,
            platform_name="iOS 17.5",
            platform="iOS 17.5",
            client_name="Safari",
            client="Safari",
        )

    def test_list_devices_returns_only_current_user_devices(self):
        response = self.client.get("/api/devices/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            set(response.data[0].keys()),
            {
                "id",
                "display_name",
                "icon",
                "ip",
                "last_seen",
                "computed_status",
                "is_current",
                "revoked_at",
                "revoked_reason",
                "platform",
                "client",
                "meta",
            },
        )
        self.assertEqual(response.data[0]["display_name"], "Windows PC")
        self.assertEqual(response.data[0]["meta"], "Windows 11 · Chrome 125")
        self.assertEqual(response.data[0]["computed_status"], "active")
        self.assertTrue(response.data[0]["is_current"])

    def test_revoke_device_marks_device_revoked(self):
        response = self.client.post(
            f"/api/devices/{self.device.id}/revoke/",
            {"reason": "Потерян ноутбук"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.revoked_at)
        self.assertEqual(self.device.status, Device.Status.REVOKED)
        self.assertEqual(self.device.revoked_reason, "Потерян ноутбук")
        self.assertTrue(
            UserActivity.objects.filter(
                user=self.user,
                action=UserActivity.Action.DEVICE_REVOKED,
                metadata__device_id=self.device.id,
            ).exists()
        )

        list_response = self.client.get("/api/devices/")
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["computed_status"], "revoked")

    def test_revoke_device_rejects_foreign_device(self):
        response = self.client.post(f"/api/devices/{self.other_device.id}/revoke/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "NOT_FOUND")

    def test_list_devices_returns_empty_list_for_user_without_devices(self):
        self.device.delete()

        response = self.client.get("/api/devices/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_list_devices_returns_stale_device_state(self):
        stale_device = Device.objects.create(
            user=self.user,
            name="Old Phone",
            display_name="Old Phone",
            icon=Device.Icon.MOBILE,
            ip_address="192.168.1.120",
            last_seen=timezone.now() - timedelta(days=31),
            status=Device.Status.STALE,
            platform_name="Android",
            platform="Android",
            client_name="Firefox",
            client="Firefox",
        )

        response = self.client.get("/api/devices/")

        resolved = next(item for item in response.data if item["id"] == stale_device.id)
        self.assertEqual(resolved["computed_status"], "stale")
