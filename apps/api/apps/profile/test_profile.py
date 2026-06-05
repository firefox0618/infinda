from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.activity.models import UserActivity


User = get_user_model()


class ProfileApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profile-user",
            email="profile@example.com",
            password="strong-pass-123",
            first_name="Rudolf",
            last_name="Naumow",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_profile_returns_current_user_data(self):
        response = self.client.get("/api/profile/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"id", "username", "email", "first_name", "last_name", "telegram_handle"},
        )
        self.assertEqual(response.data["email"], "profile@example.com")
        self.assertEqual(response.data["first_name"], "Rudolf")
        self.assertEqual(response.data["telegram_handle"], "")

    def test_patch_profile_updates_user_and_profile(self):
        response = self.client.patch(
            "/api/profile/me/",
            {
                "email": "new@example.com",
                "first_name": "Rudolf",
                "last_name": "Naumow",
                "telegram_handle": "@rudolf",
                "current_password": "strong-pass-123",
                "new_password": "updated-pass-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(self.user.first_name, "Rudolf")
        self.assertEqual(self.user.last_name, "Naumow")
        self.assertTrue(self.user.check_password("updated-pass-123"))
        self.assertEqual(response.data["telegram_handle"], "@rudolf")
        self.assertTrue(
            UserActivity.objects.filter(
                user=self.user,
                action=UserActivity.Action.PROFILE_UPDATED,
            ).exists()
        )

    def test_patch_profile_rejects_password_change_without_current_password(self):
        response = self.client.patch(
            "/api/profile/me/",
            {
                "new_password": "updated-pass-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("current_password", response.data["error"]["details"])

    def test_patch_profile_rejects_invalid_current_password(self):
        response = self.client.patch(
            "/api/profile/me/",
            {
                "current_password": "wrong-pass",
                "new_password": "updated-pass-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("current_password", response.data["error"]["details"])
