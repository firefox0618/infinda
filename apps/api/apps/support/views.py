from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.services import get_request_ip

from .models import SupportConversation
from .serializers import (
    CreateSupportMessageSerializer,
    OperatorSupportAssignSerializer,
    OperatorSupportReplySerializer,
    serialize_operator_support_conversation,
    serialize_support_conversation,
)
from .services import (
    assign_support_conversation_to_admin,
    close_support_conversation,
    create_support_message_from_user,
    get_support_conversation,
    list_support_conversations_for_admin,
    reply_to_support_conversation,
)


User = get_user_model()


class CurrentSupportConversationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversation = get_support_conversation(user=request.user)
        return Response(
            serialize_support_conversation(conversation=conversation, request=request),
            status=status.HTTP_200_OK,
        )


class SupportMessageCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        payload = request.data.copy()
        payload.setlist("attachments", request.FILES.getlist("attachments"))
        serializer = CreateSupportMessageSerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        conversation = create_support_message_from_user(
            user=request.user,
            text=serializer.validated_data.get("text", ""),
            attachments=list(serializer.validated_data.get("attachments", [])),
            ip_address=get_request_ip(request),
        )
        return Response(
            serialize_support_conversation(conversation=conversation, request=request),
            status=status.HTTP_201_CREATED,
        )


class AdminSupportConversationListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        conversations = list_support_conversations_for_admin(
            status=str(request.query_params.get("status", "")).strip() or None,
            assigned_to=str(request.query_params.get("assigned_to", "")).strip() or None,
            admin_user=request.user,
        )
        return Response(
            [
                serialize_operator_support_conversation(conversation=conversation, request=request)
                for conversation in conversations
            ],
            status=status.HTTP_200_OK,
        )


class AdminSupportConversationAssignView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, conversation_id: int):
        conversation = get_object_or_404(
            SupportConversation.objects.select_related("user", "assigned_admin").prefetch_related("messages__attachments"),
            pk=conversation_id,
        )
        serializer = OperatorSupportAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_admin = request.user
        target_admin_id = serializer.validated_data.get("admin_user_id")
        if target_admin_id is not None:
            target_admin = get_object_or_404(User.objects.filter(is_staff=True), pk=target_admin_id)
        assign_support_conversation_to_admin(
            conversation=conversation,
            admin_user=target_admin,
        )
        conversation = get_support_conversation(user=conversation.user)
        return Response(
            serialize_operator_support_conversation(conversation=conversation, request=request),
            status=status.HTTP_200_OK,
        )


class AdminSupportConversationReplyView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, conversation_id: int):
        conversation = get_object_or_404(
            SupportConversation.objects.select_related("user", "assigned_admin").prefetch_related("messages__attachments"),
            pk=conversation_id,
        )
        payload = request.data.copy()
        payload.setlist("attachments", request.FILES.getlist("attachments"))
        serializer = OperatorSupportReplySerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        conversation = reply_to_support_conversation(
            admin_user=request.user,
            conversation=conversation,
            text=serializer.validated_data.get("text", ""),
            attachments=list(serializer.validated_data.get("attachments", [])),
            assign_to_admin=False,
            close_after_reply=serializer.validated_data.get("close_after_reply", False),
        )
        return Response(
            serialize_operator_support_conversation(conversation=conversation, request=request),
            status=status.HTTP_200_OK,
        )


class AdminSupportConversationCloseView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, conversation_id: int):
        conversation = get_object_or_404(
            SupportConversation.objects.select_related("user", "assigned_admin").prefetch_related("messages__attachments"),
            pk=conversation_id,
        )
        close_support_conversation(
            conversation=conversation,
            closed_by=request.user,
        )
        conversation = get_support_conversation(user=conversation.user)
        return Response(
            serialize_operator_support_conversation(conversation=conversation, request=request),
            status=status.HTTP_200_OK,
        )
