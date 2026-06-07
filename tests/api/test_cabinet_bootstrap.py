from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.subscription.services import (
    SUBSCRIPTION_STATUS_TRIAL,
    TRIAL_MAX_DEVICES,
    TRIAL_PLAN_NAME,
)


User = get_user_model()


class CabinetBootstrapIntegrationTests(APITestCase):
    def test_register_then_login_then_bootstrap_cabinet_endpoints(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Integration User",
                "email": "integration@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register_response.data["user"]["email"], "integration@example.com")

        created_user = User.objects.get(email="integration@example.com")
        self.assertEqual(created_user.first_name, "Integration")
        self.assertEqual(created_user.last_name, "User")

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "integration@example.com",
                "password": "strong-pass-123",
            },
            format="json",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("token", login_response.data)
        token = login_response.data["token"]
        self.assertTrue(Token.objects.filter(key=token, user=created_user).exists())

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "integration@example.com")

        profile_response = self.client.get("/api/profile/me/")
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], "integration@example.com")
        self.assertEqual(profile_response.data["telegram_handle"], "")

        devices_response = self.client.get("/api/devices/")
        self.assertEqual(devices_response.status_code, status.HTTP_200_OK)
        self.assertEqual(devices_response.data, [])

        subscription_response = self.client.get("/api/subscription/")
        self.assertEqual(subscription_response.status_code, status.HTTP_200_OK)
        self.assertEqual(subscription_response.data["status"], SUBSCRIPTION_STATUS_TRIAL)
        self.assertEqual(subscription_response.data["plan_name"], TRIAL_PLAN_NAME)
        self.assertEqual(subscription_response.data["max_devices"], TRIAL_MAX_DEVICES)
        self.assertTrue(subscription_response.data["is_trial"])
        self.assertEqual(len(subscription_response.data["countries"]), 3)

        support_response = self.client.get("/api/support/conversation/")
        self.assertEqual(support_response.status_code, status.HTTP_200_OK)
        self.assertEqual(support_response.data["status"], "new")
        self.assertEqual(support_response.data["messages"], [])

        telegram_response = self.client.get("/api/telegram/link/")
        self.assertEqual(telegram_response.status_code, status.HTTP_200_OK)
        self.assertFalse(telegram_response.data["is_linked"])
        self.assertIsNone(telegram_response.data["telegram_user_id"])
