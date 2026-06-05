from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.services import get_request_ip

from .serializers import UpdateProfileSerializer, serialize_profile
from .services import get_or_create_profile, update_profile


class MeProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_or_create_profile(user=request.user)
        return Response(
            serialize_profile(user=request.user, profile=profile),
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        profile = update_profile(
            user=request.user,
            data=serializer.validated_data,
            ip_address=get_request_ip(request),
        )
        request.user.refresh_from_db()

        return Response(
            serialize_profile(user=request.user, profile=profile),
            status=status.HTTP_200_OK,
        )
