from django.conf import settings
from rest_framework import permissions, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    SubscriptionCheckoutSerializer,
    SubscriptionCheckoutRequestSerializer,
    SubscriptionPlanSerializer,
    serialize_subscription,
)
from .platega import PlategaClient, PlategaError
from .services import (
    confirm_subscription_payment_from_platega,
    create_subscription_checkout,
    get_user_subscription,
    list_subscription_plans,
)


class CurrentSubscriptionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription = get_user_subscription(user=request.user)
        return Response(
            serialize_subscription(subscription=subscription, user=request.user),
            status=status.HTTP_200_OK,
        )


class SubscriptionPlansView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            SubscriptionPlanSerializer(list_subscription_plans(), many=True).data,
            status=status.HTTP_200_OK,
        )


class SubscriptionCheckoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubscriptionCheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = create_subscription_checkout(
            user=request.user,
            plan_code=serializer.validated_data["plan_code"],
        )
        return Response(
            SubscriptionCheckoutSerializer(
                {
                    "payment_id": payment.id,
                    "checkout_url": payment.checkout_url,
                    "status": payment.status,
                    "provider": payment.provider,
                    "payment_method": payment.payment_method,
                    "plan_code": payment.plan_code,
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class DisableAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return None


class PlategaWebhookView(APIView):
    authentication_classes = [DisableAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request, secret: str):
        expected_secret = settings.PLATEGA_WEBHOOK_SECRET
        if not expected_secret or secret != expected_secret:
            return Response(
                {"ok": False, "error": "invalid secret"},
                status=status.HTTP_404_NOT_FOUND,
            )

        client = PlategaClient()
        if not client.configured:
            return Response(
                {"ok": False, "error": "platega disabled"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            payload = client.validate_callback(
                headers=dict(request.headers),
                body=request.body,
            )
            parsed_payload = client.parse_payload(payload.get("payload"))
            payment = confirm_subscription_payment_from_platega(
                callback_payload=payload,
                parsed_payload=parsed_payload,
            )
        except PlategaError as exc:
            return Response(
                {"ok": False, "error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except ValidationError as exc:
            return Response(
                {"ok": False, "error": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "ok": True,
                "payment_id": payment.id,
                "payment_status": payment.status,
                "provider_status": payment.provider_status,
            },
            status=status.HTTP_200_OK,
        )
