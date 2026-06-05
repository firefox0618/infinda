from django.contrib.auth import login, logout
from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.models import UserActivity
from apps.activity.services import get_request_ip, log_user_activity

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .services import authenticate_user, issue_auth_token, register_user, revoke_auth_token


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate_user(**serializer.validated_data)
        token = issue_auth_token(user=user)
        login(request, user)
        log_user_activity(
            user=user,
            action=UserActivity.Action.LOGIN,
            description="Пользователь вошел в систему.",
            ip_address=get_request_ip(request),
        )

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_user(**serializer.validated_data)

        return Response(
            {
                "message": "Пользователь зарегистрирован. Теперь можно войти.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        log_user_activity(
            user=request.user,
            action=UserActivity.Action.LOGOUT,
            description="Пользователь завершил сеанс.",
            ip_address=get_request_ip(request),
        )
        revoke_auth_token(user=request.user)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
