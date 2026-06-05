from django.contrib.auth import authenticate, get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


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
