from django.contrib.auth import get_user_model

from .models import UserActivity


User = get_user_model()


def get_request_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.META.get("HTTP_X_REAL_IP")
    if real_ip:
        return real_ip.strip()

    return request.META.get("REMOTE_ADDR")


def get_request_device_key(request) -> str | None:
    raw_value = request.META.get("HTTP_X_DEVICE_KEY") or request.headers.get("X-Device-Key")
    normalized = str(raw_value or "").strip()
    return normalized[:64] if normalized else None


def log_user_activity(
    *,
    user: User,
    action: UserActivity.Action,
    description: str,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> UserActivity:
    return UserActivity.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        metadata=metadata or {},
    )
