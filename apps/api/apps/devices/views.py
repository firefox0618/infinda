from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

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
        return Response(DeviceSerializer(device).data, status=status.HTTP_200_OK)
