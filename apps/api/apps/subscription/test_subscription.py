from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Subscription, SubscriptionRoute


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

        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_name="12 месяцев (безлимит)",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=365),
            max_devices=10,
            main_url="https://infinda.com/sub/main-abc123",
        )
        SubscriptionRoute.objects.bulk_create(
            [
                SubscriptionRoute(
                    subscription=self.subscription,
                    code="ru",
                    label="Россия",
                    url="https://infinda.com/sub/ru-abc123",
                    position=1,
                ),
                SubscriptionRoute(
                    subscription=self.subscription,
                    code="de",
                    label="Германия",
                    url="https://infinda.com/sub/de-abc123",
                    position=2,
                ),
            ]
        )
        Subscription.objects.create(
            user=self.other_user,
            plan_name="1 месяц",
            starts_at=timezone.localdate(),
            ends_at=timezone.localdate() + timedelta(days=30),
            max_devices=3,
            main_url="https://infinda.com/sub/other-xyz",
        )

    def test_get_subscription_returns_current_user_data(self):
        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["plan_name"], "12 месяцев (безлимит)")
        self.assertEqual(response.data["main_link"], "https://infinda.com/sub/main-abc123")
        self.assertEqual(response.data["max_devices"], 10)
        self.assertEqual(len(response.data["countries"]), 2)
        self.assertEqual(response.data["countries"][0]["code"], "ru")

    def test_get_subscription_requires_existing_subscription(self):
        self.subscription.delete()

        response = self.client.get("/api/subscription/")

        self.assertEqual(response.status_code, 404)
