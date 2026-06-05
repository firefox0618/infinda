from django.contrib.auth import get_user_model
from django.db import transaction

from .models import UserProfile


User = get_user_model()


def get_or_create_profile(*, user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def update_profile(*, user: User, data: dict) -> UserProfile:
    profile = get_or_create_profile(user=user)

    if "email" in data:
        user.email = data["email"]
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
    return profile
