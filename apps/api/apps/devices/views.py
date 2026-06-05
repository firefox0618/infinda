from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import UserActivity
from apps.activity.services import get_request_ip, log_user_activity

from .serializers import DeviceSerializer
from .services import list_user_devices, revoke_user_device


class DeviceListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        devices = list_user_devices(user=request.user)
        return Response(DeviceSerializer(devices, many=True).data, status=status.HTTP_200_OK)


class DeviceRevokeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, device_id: int):
        device = revoke_user_device(user=request.user, device_id=device_id)
        log_user_activity(
            user=request.user,
            action=UserActivity.Action.DEVICE_REVOKED,
            description=f"Пользователь отозвал устройство {device.name}.",
            ip_address=get_request_ip(request),
            metadata={"device_id": device.id, "device_name": device.name},
        )
        return Response(DeviceSerializer(device).data, status=status.HTTP_200_OK)
