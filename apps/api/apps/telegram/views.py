from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from .serializers import (
    TelegramConfirmLinkSerializer,
    TelegramLinkTokenSerializer,
    serialize_telegram_link_status,
)
from .services import (
    build_telegram_deep_link,
    confirm_telegram_link,
    create_telegram_link_token,
    get_telegram_link_status,
    unlink_telegram_account,
)


class TelegramLinkStatusView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = get_telegram_link_status(
            user=request.user,
            bot_username=settings.TELEGRAM_MAIN_BOT_USERNAME,
        )
        return Response(
            serialize_telegram_link_status(**payload),
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        token = create_telegram_link_token(
            user=request.user,
            bot_username=settings.TELEGRAM_MAIN_BOT_USERNAME,
        )
        return Response(
            TelegramLinkTokenSerializer(
                {
                    "token": token.token,
                    "deep_link_url": build_telegram_deep_link(
                        token=token.token,
                        bot_username=settings.TELEGRAM_MAIN_BOT_USERNAME,
                    ),
                    "expires_at": token.expires_at,
                }
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request):
        unlink_telegram_account(user=request.user)
        payload = get_telegram_link_status(
            user=request.user,
            bot_username=settings.TELEGRAM_MAIN_BOT_USERNAME,
        )
        return Response(
            serialize_telegram_link_status(**payload),
            status=status.HTTP_200_OK,
        )


class TelegramLinkConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TelegramConfirmLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        link = confirm_telegram_link(**serializer.validated_data)
        return Response(
            {
                "ok": True,
                "user_id": link.user_id,
                "telegram_user_id": link.telegram_user_id,
            },
            status=status.HTTP_200_OK,
        )

