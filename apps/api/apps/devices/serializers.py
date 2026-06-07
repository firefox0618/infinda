from rest_framework import serializers

from .models import Device
from .services import resolve_device_computed_status


class DeviceSerializer(serializers.ModelSerializer):
    ip = serializers.CharField(source="ip_address", read_only=True)
    meta = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    computed_status = serializers.SerializerMethodField()
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "display_name",
            "icon",
            "ip",
            "last_seen",
            "computed_status",
            "is_current",
            "revoked_at",
            "revoked_reason",
            "platform",
            "client",
            "meta",
        )

    def get_meta(self, obj: Device) -> str:
        return f"{obj.resolved_platform} · {obj.resolved_client}"

    def get_display_name(self, obj: Device) -> str:
        return obj.resolved_display_name

    def get_platform(self, obj: Device) -> str:
        return obj.resolved_platform

    def get_client(self, obj: Device) -> str:
        return obj.resolved_client

    def get_computed_status(self, obj: Device) -> str:
        return resolve_device_computed_status(device=obj)


class DeviceRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)
