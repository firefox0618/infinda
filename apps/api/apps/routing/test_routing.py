from django.test import TestCase

from apps.servers.models import Server

from .services import ensure_default_route_catalog, list_active_connection_routes


class RoutingDomainTests(TestCase):
    def test_default_route_catalog_creates_managed_routes_and_servers(self):
        routes = ensure_default_route_catalog()

        self.assertEqual(len(routes), 4)
        self.assertEqual(list_active_connection_routes().count(), 4)
        self.assertEqual(Server.objects.count(), 4)
