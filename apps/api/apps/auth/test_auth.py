from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.activity.models import UserActivity
from apps.subscription.models import Subscription
from apps.subscription.services import (
    TRIAL_MAX_DEVICES,
    TRIAL_PLAN_NAME,
    TRIAL_SUBSCRIPTION_DAYS,
)


User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.password = "infinda123"
        self.user = User.objects.create_user(
            username="alexey",
            email="alexey@infinda.com",
            password=self.password,
            first_name="Алексей",
        )

    def test_login_returns_token_and_user(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertTrue(
            UserActivity.objects.filter(
                user=self.user,
                action=UserActivity.Action.LOGIN,
            ).exists()
        )

    def test_register_creates_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Ivan Petrov",
                "email": "ivan@example.com",
                "password": "strong-pass-456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], "ivan@example.com")
        created_user = User.objects.get(email="ivan@example.com")
        self.assertEqual(created_user.first_name, "Ivan")
        self.assertEqual(created_user.last_name, "Petrov")
        created_subscription = Subscription.objects.get(user=created_user)
        self.assertEqual(created_subscription.plan_name, TRIAL_PLAN_NAME)
        self.assertEqual(created_subscription.max_devices, TRIAL_MAX_DEVICES)
        self.assertEqual(created_subscription.remaining_days, TRIAL_SUBSCRIPTION_DAYS)
        self.assertEqual(created_subscription.routes.count(), 3)

    def test_register_rejects_duplicate_email(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Alexey",
                "email": self.user.email,
                "password": "strong-pass-456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("email", response.data["error"]["details"])

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "AUTHENTICATION_FAILED")
        self.assertEqual(
            response.data["error"]["message"],
            "Неверный email или пароль.",
        )

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "NOT_AUTHENTICATED")

    def test_me_returns_current_user(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_logout_revokes_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
        self.assertTrue(
            UserActivity.objects.filter(
                user=self.user,
                action=UserActivity.Action.LOGOUT,
            ).exists()
        )
