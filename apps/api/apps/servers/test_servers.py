from django.test import TestCase

from .models import Server
from .services import create_server_status_snapshot, get_or_create_server_location


class ServerDomainTests(TestCase):
    def test_create_server_location_and_snapshot_updates_server(self):
        location = get_or_create_server_location(
            code="de-fra-custom",
            name="Germany Frankfurt Custom",
            region="Europe",
            country_code="DE",
        )
        server = Server.objects.create(
            code="de-fra-custom-1",
            name="Germany Custom 1",
            location=location,
            provider="Hetzner",
            hostname="de-fra-custom-1.infinda.local",
            ip_address="10.10.10.10",
            status=Server.Status.ACTIVE,
            capacity_units=100,
            used_capacity_units=20,
        )

        snapshot = create_server_status_snapshot(
            server=server,
            status=Server.Status.DEGRADED,
            latency_ms=180,
            active_connections=58,
            error_reason="Packet loss",
        )

        server.refresh_from_db()
        self.assertEqual(snapshot.status, Server.Status.DEGRADED)
        self.assertEqual(server.status, Server.Status.DEGRADED)
        self.assertEqual(server.status_snapshots.count(), 1)
