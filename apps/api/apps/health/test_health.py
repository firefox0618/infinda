from django.test import TestCase
from django.urls import reverse

from apps.routing.services import ensure_default_route_catalog
from apps.servers.models import Server


class HealthCheckViewTests(TestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["service"], "api")
        self.assertIn("runtime", response.json())

    def test_health_check_returns_degraded_when_offline_servers_exist(self):
        ensure_default_route_catalog()
        Server.objects.update(status=Server.Status.OFFLINE)

        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertEqual(response.json()["runtime"]["offline_server_count"], Server.objects.count())
