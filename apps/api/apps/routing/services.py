from apps.servers.models import Server
from apps.servers.services import get_or_create_server_location

from .models import ConnectionRoute, ProductLocation


DEFAULT_LOCATION_CATALOG = (
    {
        "code": "ru",
        "name": "Россия",
        "region": "Europe",
        "country_code": "RU",
        "server_code": "ru-mow-1",
        "server_name": "Russia Moscow 1",
        "provider": "INFINDA Edge",
        "hostname": "ru-mow-1.infinda.local",
        "ip_address": "10.0.0.1",
    },
    {
        "code": "de",
        "name": "Германия",
        "region": "Europe",
        "country_code": "DE",
        "server_code": "de-fra-1",
        "server_name": "Germany Frankfurt 1",
        "provider": "Hetzner",
        "hostname": "de-fra-1.infinda.local",
        "ip_address": "10.0.0.2",
    },
    {
        "code": "nl",
        "name": "Нидерланды",
        "region": "Europe",
        "country_code": "NL",
        "server_code": "nl-ams-1",
        "server_name": "Netherlands Amsterdam 1",
        "provider": "Leaseweb",
        "hostname": "nl-ams-1.infinda.local",
        "ip_address": "10.0.0.3",
    },
    {
        "code": "pl",
        "name": "Польша",
        "region": "Europe",
        "country_code": "PL",
        "server_code": "pl-waw-1",
        "server_name": "Poland Warsaw 1",
        "provider": "OVH",
        "hostname": "pl-waw-1.infinda.local",
        "ip_address": "10.0.0.4",
    },
)


def ensure_product_location(*, code: str, name: str, sort_order: int) -> ProductLocation:
    location, _created = ProductLocation.objects.get_or_create(
        code=code,
        defaults={
            "name": name,
            "sort_order": sort_order,
            "is_active": True,
        },
    )
    return location


def ensure_connection_route(
    *,
    code: str,
    name: str,
    location: ProductLocation,
    server: Server,
    endpoint_url: str,
    priority: int,
) -> ConnectionRoute:
    route, _created = ConnectionRoute.objects.get_or_create(
        code=code,
        defaults={
            "name": name,
            "location": location,
            "server": server,
            "endpoint_url": endpoint_url,
            "priority": priority,
            "is_active": True,
        },
    )
    return route


def ensure_default_route_catalog() -> list[ConnectionRoute]:
    routes: list[ConnectionRoute] = []

    for index, item in enumerate(DEFAULT_LOCATION_CATALOG, start=1):
        server_location = get_or_create_server_location(
            code=item["code"],
            name=item["name"],
            region=item["region"],
            country_code=item["country_code"],
        )
        product_location = ensure_product_location(
            code=item["code"],
            name=item["name"],
            sort_order=index,
        )
        server, _server_created = Server.objects.get_or_create(
            code=item["server_code"],
            defaults={
                "name": item["server_name"],
                "location": server_location,
                "provider": item["provider"],
                "hostname": item["hostname"],
                "ip_address": item["ip_address"],
                "status": Server.Status.ACTIVE,
                "capacity_units": 100,
                "used_capacity_units": 0,
            },
        )
        route = ensure_connection_route(
            code=item["code"],
            name=item["name"],
            location=product_location,
            server=server,
            endpoint_url=f"https://infinda.com/sub/default/{item['code']}",
            priority=index,
        )
        routes.append(route)

    return routes


def get_connection_route_by_code(*, code: str) -> ConnectionRoute:
    return ConnectionRoute.objects.select_related("location", "server").get(code=code)


def list_active_connection_routes():
    return (
        ConnectionRoute.objects.select_related("location", "server")
        .filter(is_active=True, location__is_active=True)
        .order_by("priority", "id")
    )
