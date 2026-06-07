from .models import Server, ServerLocation, ServerStatusSnapshot


def create_server_status_snapshot(
    *,
    server: Server,
    status: str,
    latency_ms: int | None = None,
    active_connections: int = 0,
    error_reason: str = "",
) -> ServerStatusSnapshot:
    snapshot = ServerStatusSnapshot.objects.create(
        server=server,
        status=status,
        latency_ms=latency_ms,
        active_connections=active_connections,
        error_reason=error_reason.strip(),
    )
    server.status = status
    server.last_heartbeat = snapshot.checked_at
    server.save(update_fields=["status", "last_heartbeat", "updated_at"])
    return snapshot


def get_or_create_server_location(
    *,
    code: str,
    name: str,
    region: str = "",
    country_code: str = "",
) -> ServerLocation:
    location, _created = ServerLocation.objects.get_or_create(
        code=code,
        defaults={
            "name": name,
            "region": region,
            "country_code": country_code,
        },
    )
    return location
