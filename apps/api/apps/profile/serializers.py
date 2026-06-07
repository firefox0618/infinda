from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile


User = get_user_model()


class ProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    telegram_handle = serializers.CharField(allow_blank=True)


class UpdateProfileSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    telegram_handle = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=64,
    )
    current_password = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=False,
        write_only=True,
    )
    new_password = serializers.CharField(
        required=False,
        allow_blank=False,
        min_length=6,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_email(self, value: str):
        normalized_email = value.strip().lower()
        user = self.context["request"].user

        if (
            User.objects.filter(email__iexact=normalized_email)
            .exclude(pk=user.pk)
            .exists()
        ):
            raise serializers.ValidationError("Пользователь с таким email уже существует.")

        return normalized_email

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        current_password = attrs.get("current_password")
        user = self.context["request"].user

        if new_password and not current_password:
            raise serializers.ValidationError(
                {"current_password": "Введите текущий пароль."},
            )

        if current_password and not new_password:
            raise serializers.ValidationError(
                {"new_password": "Введите новый пароль."},
            )

        if current_password and not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Текущий пароль введен неверно."},
            )

        if new_password:
            validate_password(new_password, user=user)

        return attrs


def serialize_profile(*, user: User, profile: UserProfile) -> dict:
    return ProfileSerializer(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telegram_handle": profile.telegram_handle,
        }
    ).data
