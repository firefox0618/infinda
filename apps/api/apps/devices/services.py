from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Device


def list_user_devices(*, user):
    return Device.objects.filter(user=user, revoked_at__isnull=True)


def revoke_user_device(*, user, device_id: int) -> Device:
    device = get_object_or_404(
        Device.objects.filter(user=user, revoked_at__isnull=True),
        pk=device_id,
    )
    device.revoked_at = timezone.now()
    device.status = Device.Status.OFFLINE
    device.save(update_fields=["revoked_at", "status", "updated_at"])
    return device
