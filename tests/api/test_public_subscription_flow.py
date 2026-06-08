from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.subscription.models import Subscription


User = get_user_model()


class PublicSubscriptionFlowIntegrationTests(APITestCase):
    def test_public_touch_then_summary_feed_and_cabinet_access_use_provisioned_device_context(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Public Flow User",
                "email": "public-flow@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="public-flow@example.com")
        subscription = Subscription.objects.get(user=user)
        route_count = subscription.routes.count()

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "public-flow@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login_response.data['token']}")

        summary_before_response = self.client.get(
            f"/api/subscription/public/{subscription.public_token}/summary/",
            REMOTE_ADDR="198.51.100.77",
        )

        self.assertEqual(summary_before_response.status_code, status.HTTP_200_OK)
        self.assertFalse(summary_before_response.data["uses_provisioned_access"])
        self.assertEqual(summary_before_response.data["provisioned_route_count"], 0)
        self.assertIsNone(summary_before_response.data["resolved_device_name"])
        self.assertEqual(len(summary_before_response.data["countries"]), route_count)
        self.assertTrue(
            all(not route["is_provisioned"] for route in summary_before_response.data["countries"])
        )

        touch_response = self.client.post(
            f"/api/subscription/public/{subscription.public_token}/touch/",
            {
                "device_name": "MacBook Air",
                "platform": "macOS",
                "client": "Happ",
                "icon": "laptop",
            },
            REMOTE_ADDR="198.51.100.77",
            HTTP_X_DEVICE_KEY="public-flow-device-key",
            format="json",
        )

        self.assertEqual(touch_response.status_code, status.HTTP_200_OK)
        self.assertTrue(touch_response.data["ok"])
        self.assertTrue(touch_response.data["created"])
        self.assertEqual(touch_response.data["device"]["display_name"], "MacBook Air")
        self.assertEqual(touch_response.data["scheduled_operation_count"], route_count)
        self.assertEqual(touch_response.data["failed_operation_count"], 0)

        summary_after_response = self.client.get(
            f"/api/subscription/public/{subscription.public_token}/summary/",
            REMOTE_ADDR="198.51.100.77",
            HTTP_X_DEVICE_KEY="public-flow-device-key",
        )
        feed_response = self.client.get(
            f"/api/subscription/public/{subscription.public_token}/feed/",
            REMOTE_ADDR="198.51.100.77",
            HTTP_X_DEVICE_KEY="public-flow-device-key",
        )

        self.assertEqual(summary_after_response.status_code, status.HTTP_200_OK)
        self.assertEqual(feed_response.status_code, status.HTTP_200_OK)
        self.assertTrue(summary_after_response.data["uses_provisioned_access"])
        self.assertEqual(summary_after_response.data["provisioned_route_count"], route_count)
        self.assertEqual(summary_after_response.data["resolved_device_name"], "MacBook Air")
        self.assertTrue(
            all(route["is_provisioned"] for route in summary_after_response.data["countries"])
        )
        self.assertEqual(
            feed_response.content.decode("utf-8").strip().splitlines(),
            [route["url"] for route in summary_after_response.data["countries"]],
        )

        devices_response = self.client.get("/api/devices/", REMOTE_ADDR="198.51.100.77")
        subscription_response = self.client.get(
            "/api/subscription/",
            REMOTE_ADDR="198.51.100.77",
            HTTP_X_DEVICE_KEY="public-flow-device-key",
        )
        access_response = self.client.get("/api/access/")
        access_sync_response = self.client.post("/api/access/sync/", format="json")

        self.assertEqual(devices_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(devices_response.data), 1)
        self.assertEqual(devices_response.data[0]["display_name"], "MacBook Air")
        self.assertTrue(devices_response.data[0]["is_current"])
        self.assertEqual(devices_response.data[0]["computed_status"], "active")

        self.assertEqual(subscription_response.status_code, status.HTTP_200_OK)
        self.assertTrue(subscription_response.data["uses_provisioned_access"])
        self.assertEqual(subscription_response.data["provisioned_route_count"], route_count)
        self.assertEqual(subscription_response.data["resolved_device_name"], "MacBook Air")
        self.assertTrue(
            all(route["is_provisioned"] for route in subscription_response.data["countries"])
        )

        self.assertEqual(access_response.status_code, status.HTTP_200_OK)
        self.assertEqual(access_response.data["status"], "active")
        self.assertEqual(access_response.data["subscription_status"], "trial")
        self.assertEqual(access_response.data["active_device_count"], 1)
        self.assertEqual(access_response.data["active_provisioned_binding_count"], route_count)
        self.assertEqual(access_response.data["provisioning_issue_count"], 0)

        self.assertEqual(access_sync_response.status_code, status.HTTP_200_OK)
        self.assertEqual(access_sync_response.data["scheduled_operation_count"], route_count)
        self.assertEqual(access_sync_response.data["failed_operation_count"], 0)
