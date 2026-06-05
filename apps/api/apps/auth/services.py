from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from apps.profile.services import get_or_create_profile
from apps.subscription.services import create_trial_subscription


User = get_user_model()


def authenticate_user(*, email: str, password: str) -> User:
    user = authenticate(username=email, password=password)

    if user is not None:
        return user

    try:
        matched_user = User.objects.get(email__iexact=email)
    except User.DoesNotExist as exc:
        raise AuthenticationFailed("Неверный email или пароль.") from exc

    user = authenticate(username=matched_user.username, password=password)
    if user is None:
        raise AuthenticationFailed("Неверный email или пароль.")

    return user


def issue_auth_token(*, user: User) -> Token:
    token, _ = Token.objects.get_or_create(user=user)
    return token


def revoke_auth_token(*, user: User) -> None:
    Token.objects.filter(user=user).delete()


def register_user(*, name: str = "", email: str, password: str) -> User:
    validate_password(password)

    cleaned_email = email.strip().lower()
    name_parts = [part for part in name.strip().split() if part]
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    with transaction.atomic():
        user = User.objects.create_user(
            username=cleaned_email,
            email=cleaned_email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        get_or_create_profile(user=user)
        create_trial_subscription(user=user)

    return user
