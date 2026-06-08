from django.conf import settings
from rest_framework import permissions, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.services import get_request_device_key, get_request_ip
from apps.devices.services import PublicDeviceTouchError

from .serializers import (
    PublicSubscriptionTouchRequestSerializer,
    PublicSubscriptionTouchResponseSerializer,
    SubscriptionCheckoutSerializer,
    SubscriptionCheckoutRequestSerializer,
    SubscriptionPlanSerializer,
    serialize_public_subscription_summary,
    serialize_subscription,
)
from .platega import PlategaClient, PlategaError
from .services import (
    build_public_subscription_feed,
    confirm_subscription_payment_from_platega,
    create_subscription_checkout,
    get_public_subscription_by_token,
    get_user_subscription,
    list_subscription_plans,
    touch_public_subscription,
)


class CurrentSubscriptionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription = get_user_subscription(user=request.user)
        return Response(
            serialize_subscription(
                subscription=subscription,
                user=request.user,
                request_ip=get_request_ip(request),
                request_device_key=get_request_device_key(request),
            ),
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


class PublicSubscriptionSummaryView(APIView):
    authentication_classes = [DisableAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request, token: str):
        subscription = get_public_subscription_by_token(token=token)
        if subscription is None:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Subscription not found.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            serialize_public_subscription_summary(
                subscription=subscription,
                request_ip=get_request_ip(request),
                request_device_key=get_request_device_key(request),
            ),
            status=status.HTTP_200_OK,
        )


class PublicSubscriptionFeedView(APIView):
    authentication_classes = [DisableAuthentication]
    permission_classes = [permissions.AllowAny]

    def get(self, request, token: str):
        subscription = get_public_subscription_by_token(token=token)
        if subscription is None:
            return HttpResponse("Not Found", status=status.HTTP_404_NOT_FOUND, content_type="text/plain")

        return HttpResponse(
            build_public_subscription_feed(
                subscription=subscription,
                request_ip=get_request_ip(request),
                request_device_key=get_request_device_key(request),
            ),
            status=status.HTTP_200_OK,
            content_type="text/plain; charset=utf-8",
        )


class PublicSubscriptionTouchView(APIView):
    authentication_classes = [DisableAuthentication]
    permission_classes = [permissions.AllowAny]

    def post(self, request, token: str):
        subscription = get_public_subscription_by_token(token=token)
        if subscription is None:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Subscription not found.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PublicSubscriptionTouchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = touch_public_subscription(
                subscription=subscription,
                request_ip=get_request_ip(request),
                request_device_key=get_request_device_key(request),
                device_name=serializer.validated_data.get("device_name", ""),
                platform_name=serializer.validated_data.get("platform", ""),
                client_name=serializer.validated_data.get("client", ""),
                icon=serializer.validated_data.get("icon", ""),
                user_agent=request.headers.get("User-Agent", ""),
            )
        except PublicDeviceTouchError as exc:
            status_code = 409 if exc.code == "SUBSCRIPTION_INACTIVE" else 400
            return Response(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": getattr(exc, "details", {}),
                    }
                },
                status=status_code,
            )

        return Response(
            PublicSubscriptionTouchResponseSerializer(payload).data,
            status=status.HTTP_200_OK,
        )
