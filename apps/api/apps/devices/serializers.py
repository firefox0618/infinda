from rest_framework import serializers

from .models import Device


class DeviceSerializer(serializers.ModelSerializer):
    ip = serializers.CharField(source="ip_address", read_only=True)
    meta = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = (
            "id",
            "name",
            "icon",
            "ip",
            "last_seen",
            "status",
            "platform_name",
            "client_name",
            "meta",
        )

    def get_meta(self, obj: Device) -> str:
        return f"{obj.platform_name} · {obj.client_name}"
