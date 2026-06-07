from rest_framework import permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.services import get_request_ip

from .serializers import CreateSupportMessageSerializer, serialize_support_conversation
from .services import create_support_message_from_user, get_support_conversation


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

