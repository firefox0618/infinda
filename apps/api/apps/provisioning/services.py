from datetime import datetime, time
from uuid import uuid4

from django.utils import timezone

from apps.devices.models import Device
from apps.routing.models import ConnectionRoute
from apps.servers.models import Server
from apps.servers.services import create_server_status_snapshot
from apps.subscription.models import Subscription

from .adapters import ProvisioningAdapterError, resolve_provisioning_adapter
from .models import (
    ProvisionedDeviceAccess,
    ProvisioningOperation,
    ServerProvisioningProfile,
)

PROVISIONING_SERVER_HEARTBEAT_MAX_AGE_SECONDS = 300


def ensure_server_provisioning_profile(*, server: Server) -> ServerProvisioningProfile:
    profile, _created = ServerProvisioningProfile.objects.get_or_create(
        server=server,
        defaults={
            "adapter": ServerProvisioningProfile.Adapter.MOCK,
            "is_enabled": True,
        },
    )
    return profile


def is_server_provisioning_health_stale(*, server: Server) -> bool:
    heartbeat_age = timezone.now() - server.last_heartbeat
    return heartbeat_age.total_seconds() >= PROVISIONING_SERVER_HEARTBEAT_MAX_AGE_SECONDS


def refresh_server_provisioning_health(*, server: Server) -> dict:
    profile = ensure_server_provisioning_profile(server=server)
    if not profile.is_enabled:
        create_server_status_snapshot(
            server=server,
            status=Server.Status.MAINTENANCE,
            error_reason="Provisioning profile disabled.",
        )
        return {
            "status": Server.Status.MAINTENANCE,
            "adapter": profile.adapter,
            "latency_ms": None,
            "error_code": "PROVISIONING_DISABLED",
            "error_message": "Provisioning profile disabled.",
        }

    adapter = resolve_provisioning_adapter(profile=profile)
    try:
        result = adapter.health_check()
    except ProvisioningAdapterError as exc:
        create_server_status_snapshot(
            server=server,
            status=Server.Status.OFFLINE,
            error_reason=exc.message,
        )
        return {
            "status": Server.Status.OFFLINE,
            "adapter": profile.adapter,
            "latency_ms": None,
            "error_code": exc.code,
            "error_message": exc.message,
        }
    except Exception as exc:
        create_server_status_snapshot(
            server=server,
            status=Server.Status.OFFLINE,
            error_reason=str(exc),
        )
        return {
            "status": Server.Status.OFFLINE,
            "adapter": profile.adapter,
            "latency_ms": None,
            "error_code": "PROVISIONING_RUNTIME_ERROR",
            "error_message": str(exc),
        }

    snapshot_status = Server.Status.ACTIVE if result.is_available else Server.Status.OFFLINE
    create_server_status_snapshot(
        server=server,
        status=snapshot_status,
        latency_ms=result.latency_ms,
        error_reason=result.error_message,
    )
    return {
        "status": snapshot_status,
        "adapter": result.adapter,
        "latency_ms": result.latency_ms,
        "error_code": result.error_code,
        "error_message": result.error_message,
    }


def refresh_enabled_provisioning_servers() -> list[dict]:
    checks: list[dict] = []
    for profile in (
        ServerProvisioningProfile.objects.select_related("server")
        .filter(is_enabled=True)
        .order_by("server__code", "id")
    ):
        checks.append(
            {
                "server_id": profile.server_id,
                "server_code": profile.server.code,
                **refresh_server_provisioning_health(server=profile.server),
            }
        )
    return checks


def _build_operation_request_payload(
    *,
    subscription: Subscription | None,
    device,
    route: ConnectionRoute,
    reason: str,
) -> dict:
    return {
        "subscription_id": subscription.id if subscription is not None else None,
        "device_id": device.id if device is not None else None,
        "route_code": route.code,
        "server_code": route.server.code,
        "reason": reason.strip(),
    }


def list_subscription_provisioning_routes(*, subscription: Subscription):
    return (
        subscription.routes.select_related("connection_route__server")
        .filter(connection_route__isnull=False)
        .order_by("position", "id")
    )


def list_active_subscription_devices(*, subscription: Subscription):
    return (
        Device.objects.filter(user=subscription.user, revoked_at__isnull=True)
        .order_by("-last_seen", "-created_at")
    )


def build_subscription_access_expires_at(*, subscription: Subscription) -> datetime:
    return timezone.make_aware(datetime.combine(subscription.ends_at, time.max))


def build_provisioned_client_email(*, subscription: Subscription | None, device: Device, route: ConnectionRoute) -> str:
    return f"infinda-s{subscription.id if subscription is not None else 0}-d{device.id}-{route.code}@local"


def ensure_provisioned_device_access(
    *,
    subscription: Subscription | None,
    device: Device,
    route: ConnectionRoute,
) -> ProvisionedDeviceAccess:
    binding, created = ProvisionedDeviceAccess.objects.get_or_create(
        device=device,
        route=route,
        defaults={
            "user": device.user,
            "subscription": subscription,
            "server": route.server,
            "status": ProvisionedDeviceAccess.Status.ACTIVE,
            "external_client_uuid": str(uuid4()),
            "external_client_email": build_provisioned_client_email(
                subscription=subscription,
                device=device,
                route=route,
            ),
        },
    )
    update_fields: list[str] = []
    if binding.user_id != device.user_id:
        binding.user = device.user
        update_fields.append("user")
    if binding.subscription_id != (subscription.id if subscription is not None else None):
        binding.subscription = subscription
        update_fields.append("subscription")
    if binding.server_id != route.server_id:
        binding.server = route.server
        update_fields.append("server")
    if not binding.external_client_uuid:
        binding.external_client_uuid = str(uuid4())
        update_fields.append("external_client_uuid")
    expected_email = build_provisioned_client_email(
        subscription=subscription,
        device=device,
        route=route,
    )
    if not binding.external_client_email:
        binding.external_client_email = expected_email
        update_fields.append("external_client_email")
    if created:
        return binding
    if update_fields:
        update_fields.append("updated_at")
        binding.save(update_fields=update_fields)
    return binding


def _mark_binding_failed(
    *,
    binding: ProvisionedDeviceAccess,
    adapter: str,
    code: str,
    message: str,
) -> None:
    binding.status = ProvisionedDeviceAccess.Status.ERROR
    binding.adapter = adapter
    binding.last_error_code = code
    binding.last_error_message = message
    binding.save(
        update_fields=[
            "status",
            "adapter",
            "last_error_code",
            "last_error_message",
            "updated_at",
        ]
    )


def _mark_server_runtime_failure(*, server: Server, message: str) -> None:
    create_server_status_snapshot(
        server=server,
        status=Server.Status.OFFLINE,
        error_reason=message,
    )


def _mark_binding_synced(
    *,
    binding: ProvisionedDeviceAccess,
    adapter: str,
    result,
) -> None:
    now = timezone.now()
    binding.status = ProvisionedDeviceAccess.Status.ACTIVE
    binding.adapter = adapter
    binding.external_client_uuid = result.external_client_uuid
    binding.external_client_email = result.external_client_email
    binding.external_client_id = result.external_client_id
    binding.inbound_id = int(result.inbound_id or 0)
    binding.connection_url = result.connection_url
    binding.metadata = result.metadata
    binding.last_error_code = ""
    binding.last_error_message = ""
    binding.provisioned_at = binding.provisioned_at or now
    binding.last_synced_at = now
    binding.revoked_at = None
    binding.save(
        update_fields=[
            "status",
            "adapter",
            "external_client_uuid",
            "external_client_email",
            "external_client_id",
            "inbound_id",
            "connection_url",
            "metadata",
            "last_error_code",
            "last_error_message",
            "provisioned_at",
            "last_synced_at",
            "revoked_at",
            "updated_at",
        ]
    )


def _mark_binding_revoked(*, binding: ProvisionedDeviceAccess, adapter: str) -> None:
    binding.status = ProvisionedDeviceAccess.Status.REVOKED
    binding.adapter = adapter
    binding.last_error_code = ""
    binding.last_error_message = ""
    binding.last_synced_at = timezone.now()
    binding.revoked_at = timezone.now()
    binding.save(
        update_fields=[
            "status",
            "adapter",
            "last_error_code",
            "last_error_message",
            "last_synced_at",
            "revoked_at",
            "updated_at",
        ]
    )


def _execute_sync_for_binding(
    *,
    operation: ProvisioningOperation,
    binding: ProvisionedDeviceAccess,
    access_expires_at: datetime,
) -> dict:
    profile = ensure_server_provisioning_profile(server=binding.server)
    adapter = resolve_provisioning_adapter(profile=profile)
    try:
        result = adapter.sync_binding(
            binding=binding,
            access_expires_at=access_expires_at,
            operation=operation,
        )
    except ProvisioningAdapterError as exc:
        _mark_server_runtime_failure(server=binding.server, message=exc.message)
        _mark_binding_failed(
            binding=binding,
            adapter=profile.adapter,
            code=exc.code,
            message=exc.message,
        )
        return {
            "device_id": binding.device_id,
            "status": ProvisioningOperation.Status.FAILED,
            "error_code": exc.code,
        }
    except Exception as exc:
        _mark_server_runtime_failure(server=binding.server, message=str(exc))
        _mark_binding_failed(
            binding=binding,
            adapter=profile.adapter,
            code="PROVISIONING_RUNTIME_ERROR",
            message=str(exc),
        )
        return {
            "device_id": binding.device_id,
            "status": ProvisioningOperation.Status.FAILED,
            "error_code": "PROVISIONING_RUNTIME_ERROR",
        }

    _mark_binding_synced(
        binding=binding,
        adapter=result.adapter,
        result=result,
    )
    return {
        "device_id": binding.device_id,
        "status": ProvisioningOperation.Status.SUCCEEDED,
        "binding_id": binding.id,
        "connection_url": binding.connection_url,
    }


def _execute_revoke_for_binding(
    *,
    operation: ProvisioningOperation,
    binding: ProvisionedDeviceAccess,
) -> dict:
    profile = ensure_server_provisioning_profile(server=binding.server)
    adapter = resolve_provisioning_adapter(profile=profile)
    try:
        result = adapter.revoke_binding(
            binding=binding,
            operation=operation,
        )
    except ProvisioningAdapterError as exc:
        _mark_server_runtime_failure(server=binding.server, message=exc.message)
        _mark_binding_failed(
            binding=binding,
            adapter=profile.adapter,
            code=exc.code,
            message=exc.message,
        )
        return {
            "device_id": binding.device_id,
            "status": ProvisioningOperation.Status.FAILED,
            "error_code": exc.code,
        }
    except Exception as exc:
        _mark_server_runtime_failure(server=binding.server, message=str(exc))
        _mark_binding_failed(
            binding=binding,
            adapter=profile.adapter,
            code="PROVISIONING_RUNTIME_ERROR",
            message=str(exc),
        )
        return {
            "device_id": binding.device_id,
            "status": ProvisioningOperation.Status.FAILED,
            "error_code": "PROVISIONING_RUNTIME_ERROR",
        }

    _mark_binding_revoked(binding=binding, adapter=result["adapter"])
    return {
        "device_id": binding.device_id,
        "status": ProvisioningOperation.Status.SUCCEEDED,
        "binding_id": binding.id,
    }


def execute_provisioning_operation(*, operation: ProvisioningOperation) -> ProvisioningOperation:
    if operation.route_id is None or operation.server_id is None:
        operation.mark_finished(
            status=ProvisioningOperation.Status.SKIPPED,
            error_code="MISSING_ROUTE_OR_SERVER",
            error_message="Provisioning operation requires route and server.",
        )
        return operation

    profile = ensure_server_provisioning_profile(server=operation.server)
    if not profile.is_enabled:
        operation.mark_finished(
            status=ProvisioningOperation.Status.SKIPPED,
            adapter=profile.adapter,
            error_code="PROVISIONING_DISABLED",
            error_message="Provisioning profile is disabled for this server.",
        )
        return operation

    if operation.server.status in {Server.Status.OFFLINE, Server.Status.MAINTENANCE}:
        operation.mark_finished(
            status=ProvisioningOperation.Status.FAILED,
            adapter=profile.adapter,
            error_code="SERVER_UNAVAILABLE",
            error_message="Server is not available for provisioning.",
            result_payload={
                "server_status": operation.server.status,
                "latency_ms": None,
            },
        )
        return operation

    health_result = None
    if is_server_provisioning_health_stale(server=operation.server):
        health_result = refresh_server_provisioning_health(server=operation.server)
        if operation.server.status in {Server.Status.OFFLINE, Server.Status.MAINTENANCE}:
            operation.mark_finished(
                status=ProvisioningOperation.Status.FAILED,
                adapter=profile.adapter,
                error_code=health_result["error_code"] or "SERVER_UNAVAILABLE",
                error_message=health_result["error_message"] or "Server is not available for provisioning.",
                result_payload={
                    "server_status": operation.server.status,
                    "latency_ms": health_result["latency_ms"],
                },
            )
            return operation

    if operation.subscription_id is None:
        operation.mark_finished(
            status=ProvisioningOperation.Status.SKIPPED,
            adapter=profile.adapter,
            error_code="MISSING_SUBSCRIPTION",
            error_message="Provisioning operation requires subscription.",
        )
        return operation

    if operation.operation_type == ProvisioningOperation.OperationType.REVOKE_DEVICE_ACCESS:
        if operation.device_id is None:
            operation.mark_finished(
                status=ProvisioningOperation.Status.SKIPPED,
                adapter=profile.adapter,
                error_code="MISSING_DEVICE",
                error_message="Revoke operation requires device.",
            )
            return operation

        binding = ProvisionedDeviceAccess.objects.filter(
            device=operation.device,
            route=operation.route,
        ).first()
        if binding is None:
            operation.mark_finished(
                status=ProvisioningOperation.Status.SKIPPED,
                adapter=profile.adapter,
                result_payload={"mode": "no-binding-to-revoke"},
            )
            return operation

        result_item = _execute_revoke_for_binding(operation=operation, binding=binding)
        operation.mark_finished(
            status=result_item["status"],
            adapter=profile.adapter,
            error_code=result_item.get("error_code", ""),
            error_message="" if result_item["status"] == ProvisioningOperation.Status.SUCCEEDED else "Binding revoke failed.",
            result_payload={"bindings": [result_item]},
        )
        return operation

    access_expires_at = build_subscription_access_expires_at(subscription=operation.subscription)
    if operation.device_id is not None:
        target_devices = [operation.device]
    else:
        target_devices = list(list_active_subscription_devices(subscription=operation.subscription))

    if not target_devices:
        operation.mark_finished(
            status=ProvisioningOperation.Status.SKIPPED,
            adapter=profile.adapter,
            result_payload={"bindings": [], "mode": "no-active-devices"},
        )
        return operation

    binding_results: list[dict] = []
    for device in target_devices:
        binding = ensure_provisioned_device_access(
            subscription=operation.subscription,
            device=device,
            route=operation.route,
        )
        binding_results.append(
            _execute_sync_for_binding(
                operation=operation,
                binding=binding,
                access_expires_at=access_expires_at,
            )
        )

    failed = [item for item in binding_results if item["status"] == ProvisioningOperation.Status.FAILED]
    operation.mark_finished(
        status=ProvisioningOperation.Status.FAILED if failed else ProvisioningOperation.Status.SUCCEEDED,
        adapter=profile.adapter,
        error_code=failed[0]["error_code"] if failed else "",
        error_message="One or more device bindings failed." if failed else "",
        result_payload={"bindings": binding_results},
    )
    return operation


def schedule_subscription_sync(
    *,
    subscription: Subscription,
    trigger: str,
    device=None,
    reason: str = "",
) -> list[ProvisioningOperation]:
    operations: list[ProvisioningOperation] = []
    for subscription_route in list_subscription_provisioning_routes(subscription=subscription):
        route = subscription_route.connection_route
        operation = ProvisioningOperation.objects.create(
            user=subscription.user,
            subscription=subscription,
            device=device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.SYNC_SUBSCRIPTION_ACCESS,
            trigger=trigger,
            request_payload=_build_operation_request_payload(
                subscription=subscription,
                device=device,
                route=route,
                reason=reason,
            ),
        )
        operations.append(execute_provisioning_operation(operation=operation))
    return operations


def schedule_device_revoke(
    *,
    subscription: Subscription | None,
    device,
    reason: str = "",
) -> list[ProvisioningOperation]:
    if subscription is None:
        return []

    operations: list[ProvisioningOperation] = []
    for subscription_route in list_subscription_provisioning_routes(subscription=subscription):
        route = subscription_route.connection_route
        operation = ProvisioningOperation.objects.create(
            user=subscription.user,
            subscription=subscription,
            device=device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REVOKE_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.DEVICE_REVOKED,
            request_payload=_build_operation_request_payload(
                subscription=subscription,
                device=device,
                route=route,
                reason=reason,
            ),
        )
        operations.append(execute_provisioning_operation(operation=operation))
    return operations


def schedule_device_repair(
    *,
    subscription: Subscription | None,
    device,
    reason: str = "",
) -> list[ProvisioningOperation]:
    if subscription is None:
        return []

    operations: list[ProvisioningOperation] = []
    for subscription_route in list_subscription_provisioning_routes(subscription=subscription):
        route = subscription_route.connection_route
        operation = ProvisioningOperation.objects.create(
            user=subscription.user,
            subscription=subscription,
            device=device,
            route=route,
            server=route.server,
            operation_type=ProvisioningOperation.OperationType.REPAIR_DEVICE_ACCESS,
            trigger=ProvisioningOperation.Trigger.REPAIR_REQUESTED,
            request_payload=_build_operation_request_payload(
                subscription=subscription,
                device=device,
                route=route,
                reason=reason,
            ),
        )
        operations.append(execute_provisioning_operation(operation=operation))
    return operations


def schedule_manual_subscription_sync(*, subscription: Subscription) -> list[ProvisioningOperation]:
    return schedule_subscription_sync(
        subscription=subscription,
        trigger=ProvisioningOperation.Trigger.MANUAL_SYNC,
    )


def build_user_provisioning_summary(*, user) -> dict:
    recent_operations = list(
        ProvisioningOperation.objects.filter(user=user).order_by("-created_at", "-id")[:20]
    )
    failed_operations = [item for item in recent_operations if item.status == ProvisioningOperation.Status.FAILED]
    bindings = ProvisionedDeviceAccess.objects.filter(user=user)
    unhealthy_server_count = Server.objects.filter(status__in=(Server.Status.OFFLINE, Server.Status.MAINTENANCE)).count()
    degraded_server_count = Server.objects.filter(status=Server.Status.DEGRADED).count()
    return {
        "recent_operation_count": len(recent_operations),
        "failed_operation_count": len(failed_operations),
        "last_operation_at": recent_operations[0].created_at if recent_operations else None,
        "last_error_codes": [item.error_code for item in failed_operations[:5] if item.error_code],
        "active_binding_count": bindings.filter(status=ProvisionedDeviceAccess.Status.ACTIVE).count(),
        "error_binding_count": bindings.filter(status=ProvisionedDeviceAccess.Status.ERROR).count(),
        "revoked_binding_count": bindings.filter(status=ProvisionedDeviceAccess.Status.REVOKED).count(),
        "unhealthy_server_count": unhealthy_server_count,
        "degraded_server_count": degraded_server_count,
    }
