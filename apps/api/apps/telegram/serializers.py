from rest_framework import serializers

from .models import TelegramAccountLink


class TelegramLinkStatusSerializer(serializers.Serializer):
    is_linked = serializers.BooleanField(read_only=True)
    telegram_user_id = serializers.IntegerField(read_only=True, allow_null=True)
    telegram_username = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    telegram_full_name = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    linked_at = serializers.DateTimeField(read_only=True, allow_null=True)
    pending_link_expires_at = serializers.DateTimeField(read_only=True, allow_null=True)
    pending_deep_link_url = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)


class TelegramLinkTokenSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)
    deep_link_url = serializers.CharField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)


class TelegramConfirmLinkSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)
    telegram_user_id = serializers.IntegerField()
    telegram_username = serializers.CharField(required=False, allow_blank=True, max_length=255)
    telegram_full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)


def serialize_telegram_link_status(
    *,
    link: TelegramAccountLink | None,
    pending_link_expires_at,
    pending_deep_link_url: str | None,
) -> dict:
    return TelegramLinkStatusSerializer(
        {
            "is_linked": link is not None and link.is_active,
            "telegram_user_id": link.telegram_user_id if link else None,
            "telegram_username": link.telegram_username if link else None,
            "telegram_full_name": link.telegram_full_name if link else None,
            "linked_at": link.linked_at if link else None,
            "pending_link_expires_at": pending_link_expires_at,
            "pending_deep_link_url": pending_deep_link_url,
        }
    ).data

