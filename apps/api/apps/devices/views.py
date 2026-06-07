from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import UserActivity
from apps.activity.services import get_request_ip, log_user_activity
from apps.notifications.services import dispatch_notification

from .serializers import DeviceRevokeSerializer, DeviceSerializer
from .services import list_user_devices, resolve_current_device_id, revoke_user_device


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
