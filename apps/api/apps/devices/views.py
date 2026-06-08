from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import UserActivity
from apps.activity.services import get_request_ip, log_user_activity
from apps.notifications.services import dispatch_notification
from apps.provisioning.services import schedule_device_repair, schedule_device_revoke
from apps.subscription.services import get_user_subscription

from .serializers import (
    DeviceRepairResponseSerializer,
    DeviceRepairSerializer,
    DeviceRevokeSerializer,
    DeviceSerializer,
)
from .services import (
    list_user_devices,
    repair_user_device,
    resolve_current_device_id,
    revoke_user_device,
)


class DeviceListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        current_device_id = resolve_current_device_id(
            user=request.user,
            request_ip=get_request_ip(request),
        )
        devices = [
            device
            for device in list_user_devices(user=request.user)
        ]
        for device in devices:
            device.is_current = device.id == current_device_id
        return Response(DeviceSerializer(devices, many=True).data, status=status.HTTP_200_OK)


class DeviceRevokeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, device_id: int):
        serializer = DeviceRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = revoke_user_device(
            user=request.user,
            device_id=device_id,
            reason=serializer.validated_data.get("reason", ""),
        )
        schedule_device_revoke(
            subscription=get_user_subscription(user=request.user),
            device=device,
            reason=device.revoked_reason,
        )
        log_user_activity(
            user=request.user,
            action=UserActivity.Action.DEVICE_REVOKED,
            description=f"Пользователь отозвал устройство {device.name}.",
            ip_address=get_request_ip(request),
            metadata={
                "device_id": device.id,
                "device_name": device.name,
                "revoked_reason": device.revoked_reason,
            },
        )
        dispatch_notification(
            event_type="device_revoked",
            user=request.user,
            payload={
                "device_id": device.id,
                "display_name": device.resolved_display_name,
                "platform": device.resolved_platform,
                "client": device.resolved_client,
                "revoked_reason": device.revoked_reason,
            },
        )
        device.is_current = False
        return Response(DeviceSerializer(device).data, status=status.HTTP_200_OK)


class DeviceRepairView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, device_id: int):
        serializer = DeviceRepairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = repair_user_device(
            user=request.user,
            device_id=device_id,
        )
        operations = schedule_device_repair(
            subscription=get_user_subscription(user=request.user),
            device=device,
            reason=serializer.validated_data.get("reason", ""),
        )
        current_device_id = resolve_current_device_id(
            user=request.user,
            request_ip=get_request_ip(request),
        )
        device.is_current = device.id == current_device_id
        payload = {
            "device": device,
            "scheduled_operation_count": len(operations),
            "failed_operation_count": len(
                [item for item in operations if item.status == item.Status.FAILED]
            ),
        }
        log_user_activity(
            user=request.user,
            action=UserActivity.Action.VPN_REPAIR_EVENT,
            description=f"Пользователь запросил восстановление устройства {device.name}.",
            ip_address=get_request_ip(request),
            metadata={
                "device_id": device.id,
                "device_name": device.name,
                "repair_reason": serializer.validated_data.get("reason", "").strip(),
                "scheduled_operation_count": payload["scheduled_operation_count"],
                "failed_operation_count": payload["failed_operation_count"],
            },
        )
        return Response(
            DeviceRepairResponseSerializer(payload).data,
            status=status.HTTP_200_OK,
        )
