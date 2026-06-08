from rest_framework import serializers

from .models import SupportAttachment, SupportConversation, SupportMessage


class SupportAttachmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    file_name = serializers.CharField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    size_bytes = serializers.IntegerField(read_only=True)
    url = serializers.CharField(read_only=True)


class SupportMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    sender_type = serializers.ChoiceField(choices=SupportMessage.SenderType.choices, read_only=True)
    sender_display_name = serializers.CharField(read_only=True)
    source = serializers.ChoiceField(choices=SupportMessage.Source.choices, read_only=True)
    text = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    attachments = SupportAttachmentSerializer(many=True, read_only=True)


class SupportConversationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=SupportConversation.Status.choices, read_only=True)
    assigned_admin_name = serializers.CharField(read_only=True, allow_null=True)
    last_message_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    closed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    messages = SupportMessageSerializer(many=True, read_only=True)


class OperatorSupportConversationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    user_email = serializers.EmailField(read_only=True)
    user_display_name = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(choices=SupportConversation.Status.choices, read_only=True)
    delivery_channel = serializers.ChoiceField(
        choices=(
            SupportMessage.Source.WEB,
            SupportMessage.Source.TELEGRAM_SUPPORT_BOT,
        ),
        read_only=True,
    )
    assigned_admin_id = serializers.IntegerField(read_only=True, allow_null=True)
    assigned_admin_name = serializers.CharField(read_only=True, allow_null=True)
    last_message_preview = serializers.CharField(read_only=True, allow_blank=True)
    last_message_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    closed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    messages = SupportMessageSerializer(many=True, read_only=True)


class CreateSupportMessageSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True,
    )

    def validate(self, attrs):
        text = str(attrs.get("text", "")).strip()
        attachments = attrs.get("attachments", [])

        if not text and not attachments:
            raise serializers.ValidationError(
                {"text": "Добавьте сообщение или прикрепите хотя бы один файл."},
            )

        return attrs


class OperatorSupportAssignSerializer(serializers.Serializer):
    admin_user_id = serializers.IntegerField(required=False, min_value=1)


class OperatorSupportReplySerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True,
    )
    close_after_reply = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        text = str(attrs.get("text", "")).strip()
        attachments = attrs.get("attachments", [])

        if not text and not attachments:
            raise serializers.ValidationError(
                {"text": "Добавьте сообщение или прикрепите хотя бы один файл."},
            )

        return attrs


def serialize_support_attachment(*, attachment: SupportAttachment, request) -> dict:
    attachment_url = attachment.file.url
    if request is not None:
        attachment_url = request.build_absolute_uri(attachment.file.url)

    return SupportAttachmentSerializer(
        {
            "id": attachment.id,
            "file_name": attachment.file_name,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "url": attachment_url,
        }
    ).data


def serialize_support_message(*, message: SupportMessage, request) -> dict:
    return SupportMessageSerializer(
        {
            "id": message.id,
            "sender_type": message.sender_type,
            "sender_display_name": message.sender_display_name,
            "source": message.source,
            "text": message.text,
            "created_at": message.created_at,
            "attachments": [
                serialize_support_attachment(attachment=attachment, request=request)
                for attachment in message.attachments.all()
            ],
        }
    ).data


def serialize_support_conversation(*, conversation: SupportConversation, request) -> dict:
    return SupportConversationSerializer(
        {
            "id": conversation.id,
            "status": conversation.status,
            "assigned_admin_name": conversation.assigned_admin.get_full_name() or conversation.assigned_admin.username
            if conversation.assigned_admin
            else None,
            "last_message_at": conversation.last_message_at,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "closed_at": conversation.closed_at,
            "messages": [
                serialize_support_message(message=message, request=request)
                for message in conversation.messages.all()
            ],
        }
    ).data


def serialize_operator_support_conversation(*, conversation: SupportConversation, request) -> dict:
    delivery_channel = (
        SupportMessage.Source.TELEGRAM_SUPPORT_BOT
        if any(
            message.source == SupportMessage.Source.TELEGRAM_SUPPORT_BOT
            for message in conversation.messages.all()
        )
        else SupportMessage.Source.WEB
    )
    return OperatorSupportConversationSerializer(
        {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "user_email": conversation.user.email,
            "user_display_name": (
                conversation.user.get_full_name()
                or conversation.user.username
                or conversation.user.email
            ),
            "status": conversation.status,
            "delivery_channel": delivery_channel,
            "assigned_admin_id": conversation.assigned_admin_id,
            "assigned_admin_name": (
                conversation.assigned_admin.get_full_name() or conversation.assigned_admin.username
                if conversation.assigned_admin
                else None
            ),
            "last_message_preview": conversation.last_message_preview,
            "last_message_at": conversation.last_message_at,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "closed_at": conversation.closed_at,
            "messages": [
                serialize_support_message(message=message, request=request)
                for message in conversation.messages.all()
            ],
        }
    ).data
