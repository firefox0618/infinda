from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AccessStateSerializer
from .services import build_user_access_state


class CurrentAccessStateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = build_user_access_state(user=request.user)
        return Response(AccessStateSerializer(payload).data, status=status.HTTP_200_OK)
