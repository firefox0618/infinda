from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Device


STALE_DEVICE_THRESHOLD_DAYS = 30


class PublicDeviceTouchError(Exception):
    def __init__(self, *, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def list_user_devices(*, user):
    return Device.objects.filter(user=user)


def resolve_device_computed_status(*, device: Device) -> str:
    if device.revoked_at is not None:
        return Device.Status.REVOKED

    stale_cutoff = timezone.now() - timedelta(days=STALE_DEVICE_THRESHOLD_DAYS)
    if device.last_seen < stale_cutoff:
        return Device.Status.STALE

    return Device.Status.ACTIVE


def resolve_current_device_id(*, user, request_ip: str | None) -> int | None:
    candidates = Device.objects.filter(user=user, revoked_at__isnull=True).order_by("-last_seen", "-created_at")
    if request_ip:
        matched = candidates.filter(ip_address=request_ip).first()
        if matched is not None:
            return matched.id

    fallback = candidates.first()
    return fallback.id if fallback is not None else None


def revoke_user_device(*, user, device_id: int, reason: str = "") -> Device:
    device = get_object_or_404(
        Device.objects.filter(user=user, revoked_at__isnull=True),
        pk=device_id,
    )
    device.revoked_at = timezone.now()
    device.revoked_reason = reason.strip()
    device.status = Device.Status.REVOKED
    device.save(update_fields=["revoked_at", "revoked_reason", "status", "updated_at"])
    return device


def repair_user_device(*, user, device_id: int) -> Device:
    device = get_object_or_404(
        Device.objects.filter(user=user),
        pk=device_id,
    )
    if device.revoked_at is not None:
        raise ValidationError({"device": "Нельзя восстановить уже отозванное устройство."})
    return device


def _normalize_public_device_name(*, provided_name: str, platform_name: str) -> str:
    normalized_name = provided_name.strip()
    if normalized_name:
        return normalized_name[:120]
    normalized_platform = platform_name.strip()
    if normalized_platform:
        return f"{normalized_platform} device"[:120]
    return "Current device"


def touch_public_subscription_device(
    *,
    subscription,
    request_ip: str | None,
    device_key: str = "",
    device_name: str = "",
    platform_name: str = "",
    client_name: str = "",
    icon: str = Device.Icon.DESKTOP,
) -> tuple[Device | None, bool]:
    if not request_ip:
        raise PublicDeviceTouchError(
            code="DEVICE_IP_UNAVAILABLE",
            message="Could not determine the current device IP.",
        )

    normalized_platform = (platform_name or "").strip() or "Unknown"
    normalized_client = (client_name or "").strip() or "Happ"
    normalized_icon = icon if icon in Device.Icon.values else Device.Icon.DESKTOP
    normalized_device_key = str(device_key or "").strip()[:64]
    normalized_name = _normalize_public_device_name(
        provided_name=device_name,
        platform_name=normalized_platform,
    )

    if normalized_device_key:
        existing_device = (
            Device.objects.filter(
                user=subscription.user,
                revoked_at__isnull=True,
                public_device_key=normalized_device_key,
            )
            .order_by("-last_seen", "-created_at")
            .first()
        )
    else:
        existing_device = None
    if existing_device is None:
        existing_device = (
            Device.objects.filter(
                user=subscription.user,
                revoked_at__isnull=True,
                ip_address=request_ip,
            )
            .order_by("-last_seen", "-created_at")
            .first()
        )
    if existing_device is not None:
        existing_device.last_seen = timezone.now()
        existing_device.status = Device.Status.ACTIVE
        existing_device.icon = normalized_icon
        existing_device.ip_address = request_ip
        existing_device.platform_name = normalized_platform
        existing_device.platform = normalized_platform
        existing_device.client_name = normalized_client
        existing_device.client = normalized_client
        if normalized_device_key:
            existing_device.public_device_key = normalized_device_key
        if normalized_name:
            existing_device.display_name = normalized_name
            existing_device.name = normalized_name
        elif not existing_device.display_name:
            existing_device.display_name = normalized_name
        if not existing_device.name:
            existing_device.name = normalized_name
        existing_device.save(
            update_fields=[
                "last_seen",
                "status",
                "icon",
                "ip_address",
                "platform_name",
                "platform",
                "client_name",
                "client",
                "public_device_key",
                "display_name",
                "name",
                "updated_at",
            ]
        )
        return existing_device, False

    active_device_count = Device.objects.filter(
        user=subscription.user,
        revoked_at__isnull=True,
    ).count()
    if active_device_count >= subscription.max_devices:
        raise PublicDeviceTouchError(
            code="DEVICE_LIMIT_EXCEEDED",
            message="Device limit exceeded for this subscription.",
            details={"max_devices": subscription.max_devices},
        )

    device = Device.objects.create(
        user=subscription.user,
        name=normalized_name,
        display_name=normalized_name,
        icon=normalized_icon,
        ip_address=request_ip,
        last_seen=timezone.now(),
        status=Device.Status.ACTIVE,
        platform_name=normalized_platform,
        platform=normalized_platform,
        client_name=normalized_client,
        client=normalized_client,
        public_device_key=normalized_device_key,
    )
    return device, True
