from django.contrib.auth import get_user_model
from django.db import transaction

from apps.activity.models import UserActivity
from apps.activity.services import log_user_activity

from .models import UserProfile


User = get_user_model()


def get_or_create_profile(*, user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def update_profile(*, user: User, data: dict, ip_address: str | None = None) -> UserProfile:
    profile = get_or_create_profile(user=user)

    if "email" in data:
        user.email = data["email"]
        user.username = data["email"]
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "new_password" in data:
        user.set_password(data["new_password"])

    user.save()

    if "telegram_handle" in data:
        profile.telegram_handle = data["telegram_handle"]

    profile.save()
    changed_fields = sorted(
        field_name
        for field_name in ("email", "first_name", "last_name", "telegram_handle", "new_password")
        if field_name in data
    )
    log_user_activity(
        user=user,
        action=UserActivity.Action.PROFILE_UPDATED,
        description="Пользователь обновил данные профиля.",
        ip_address=ip_address,
        metadata={"changed_fields": changed_fields},
    )
    return profile
