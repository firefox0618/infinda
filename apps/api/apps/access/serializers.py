from rest_framework import serializers


class AccessStateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=(
            "active",
            "expired",
            "pending_payment",
            "device_limit_exceeded",
            "restricted",
            "server_unavailable",
        )
    )
    reason = serializers.CharField(allow_blank=True)
    subscription_status = serializers.CharField(allow_blank=True)
    active_device_count = serializers.IntegerField()
    allowed_device_count = serializers.IntegerField()
    available_route_count = serializers.IntegerField()
    unavailable_route_codes = serializers.ListField(child=serializers.CharField())
