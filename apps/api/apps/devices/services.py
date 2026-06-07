from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Device


STALE_DEVICE_THRESHOLD_DAYS = 30


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
