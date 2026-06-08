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
    provisioning_issue_count = serializers.IntegerField()
    last_provisioning_error_codes = serializers.ListField(child=serializers.CharField())
    active_provisioned_binding_count = serializers.IntegerField()
    error_provisioned_binding_count = serializers.IntegerField()
    unhealthy_provisioning_server_count = serializers.IntegerField()
    degraded_provisioning_server_count = serializers.IntegerField()


class AccessSyncSerializer(serializers.Serializer):
    scheduled_operation_count = serializers.IntegerField()
    failed_operation_count = serializers.IntegerField()
