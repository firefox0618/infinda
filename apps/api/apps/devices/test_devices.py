from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

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
            icon=Device.Icon.DESKTOP,
            ip_address="192.168.1.101",
            last_seen=timezone.now(),
            status=Device.Status.ONLINE,
            platform_name="Windows 11",
            client_name="Chrome 125",
        )
        self.other_device = Device.objects.create(
            user=self.other_user,
            name="Other Device",
            icon=Device.Icon.MOBILE,
            ip_address="192.168.1.102",
            last_seen=timezone.now() - timedelta(hours=1),
            status=Device.Status.OFFLINE,
            platform_name="iOS 17.5",
            client_name="Safari",
        )

    def test_list_devices_returns_only_current_user_devices(self):
        response = self.client.get("/api/devices/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Windows PC")
        self.assertEqual(response.data[0]["meta"], "Windows 11 · Chrome 125")

    def test_revoke_device_marks_device_revoked(self):
        response = self.client.post(f"/api/devices/{self.device.id}/revoke/")

        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.revoked_at)
        self.assertEqual(self.device.status, Device.Status.OFFLINE)

        list_response = self.client.get("/api/devices/")
        self.assertEqual(list_response.data, [])
