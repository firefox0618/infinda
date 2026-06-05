from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import serialize_subscription
from .services import get_user_subscription


class CurrentSubscriptionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription = get_user_subscription(user=request.user)
        return Response(
            serialize_subscription(subscription=subscription),
            status=status.HTTP_200_OK,
        )
