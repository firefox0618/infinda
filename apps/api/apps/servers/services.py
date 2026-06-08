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


def build_server_runtime_summary() -> dict:
    total_server_count = Server.objects.count()
    active_server_count = Server.objects.filter(status=Server.Status.ACTIVE).count()
    degraded_server_count = Server.objects.filter(status=Server.Status.DEGRADED).count()
    offline_server_count = Server.objects.filter(status=Server.Status.OFFLINE).count()
    maintenance_server_count = Server.objects.filter(status=Server.Status.MAINTENANCE).count()
    latest_snapshot = ServerStatusSnapshot.objects.order_by("-checked_at", "-id").first()
    return {
        "total_server_count": total_server_count,
        "active_server_count": active_server_count,
        "degraded_server_count": degraded_server_count,
        "offline_server_count": offline_server_count,
        "maintenance_server_count": maintenance_server_count,
        "last_runtime_check_at": latest_snapshot.checked_at if latest_snapshot is not None else None,
    }
