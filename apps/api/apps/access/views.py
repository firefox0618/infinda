from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.provisioning.services import schedule_manual_subscription_sync
from apps.subscription.services import get_user_subscription

from .serializers import AccessStateSerializer, AccessSyncSerializer
from .services import build_user_access_state


class CurrentAccessStateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = build_user_access_state(user=request.user)
        return Response(AccessStateSerializer(payload).data, status=status.HTTP_200_OK)


class CurrentAccessSyncView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        subscription = get_user_subscription(user=request.user)
        if subscription is None:
            return Response(
                {
                    "error": {
                        "code": "NO_SUBSCRIPTION",
                        "message": "Subscription is required for sync.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        operations = schedule_manual_subscription_sync(subscription=subscription)
        payload = {
            "scheduled_operation_count": len(operations),
            "failed_operation_count": len(
                [item for item in operations if item.status == item.Status.FAILED]
            ),
        }
        return Response(AccessSyncSerializer(payload).data, status=status.HTTP_200_OK)
