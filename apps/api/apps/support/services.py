from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.activity.services import log_user_activity
from apps.notifications.services import dispatch_notification
from apps.telegram.services import (
    get_active_telegram_link,
    notify_support_team_about_ticket,
    send_telegram_document,
    send_telegram_message,
)

from .models import SupportAttachment, SupportConversation, SupportMessage


User = get_user_model()


@dataclass(frozen=True)
class IncomingSupportAttachment:
    file_name: str
    content_type: str
    content_bytes: bytes


def get_or_create_support_conversation(*, user) -> SupportConversation:
    conversation, _ = SupportConversation.objects.get_or_create(user=user)
    return (
        SupportConversation.objects.select_related("assigned_admin", "user")
        .prefetch_related("messages__attachments")
        .get(pk=conversation.pk)
    )


def get_support_conversation(*, user) -> SupportConversation:
    return get_or_create_support_conversation(user=user)


def get_last_user_support_message(*, conversation: SupportConversation) -> SupportMessage | None:
    return (
        conversation.messages.filter(sender_type=SupportMessage.SenderType.USER)
        .order_by("-created_at", "-id")
        .first()
    )


def get_support_delivery_channel(*, conversation: SupportConversation) -> str:
    last_user_message = get_last_user_support_message(conversation=conversation)
    if last_user_message and last_user_message.source == SupportMessage.Source.TELEGRAM_SUPPORT_BOT:
        return SupportMessage.Source.TELEGRAM_SUPPORT_BOT

    return SupportMessage.Source.WEB


def refresh_support_conversation_state(*, conversation: SupportConversation, message: SupportMessage) -> SupportConversation:
    preview_text = (message.text or "").strip()
    if not preview_text and message.attachments.exists():
        preview_text = "Прикреплены файлы"

    conversation.last_message_at = message.created_at
    conversation.last_message_preview = preview_text[:255]

    if message.sender_type == SupportMessage.SenderType.USER:
        if conversation.status == SupportConversation.Status.CLOSED:
            conversation.assigned_admin = None
        conversation.status = (
            SupportConversation.Status.NEW
            if conversation.assigned_admin is None
            else SupportConversation.Status.IN_PROGRESS
        )
        conversation.closed_at = None
    else:
        conversation.status = SupportConversation.Status.IN_PROGRESS
        conversation.closed_at = None
        if message.sender_user and conversation.assigned_admin_id is None:
            conversation.assigned_admin = message.sender_user

    conversation.save(
        update_fields=[
            "assigned_admin",
            "status",
            "closed_at",
            "last_message_at",
            "last_message_preview",
            "updated_at",
        ]
    )
    return conversation


@transaction.atomic
def create_support_message_from_user(
    *,
    user,
    text: str,
    attachments: list,
    ip_address: str | None = None,
) -> SupportConversation:
    conversation = get_or_create_support_conversation(user=user)
    should_notify_support_team = conversation.messages.count() == 0
    was_closed = conversation.status == SupportConversation.Status.CLOSED
    message = SupportMessage.objects.create(
        conversation=conversation,
        sender_type=SupportMessage.SenderType.USER,
        sender_user=user,
        sender_display_name="Вы",
        source=SupportMessage.Source.WEB,
        text=text.strip(),
    )

    for uploaded_file in attachments:
        SupportAttachment.objects.create(
            message=message,
            file=uploaded_file,
            file_name=uploaded_file.name,
            content_type=getattr(uploaded_file, "content_type", "") or "",
            size_bytes=getattr(uploaded_file, "size", 0) or 0,
        )

    refresh_support_conversation_state(conversation=conversation, message=message)
    log_user_activity(
        user=user,
        action="support_message_sent",
        description="Пользователь отправил сообщение в поддержку.",
        ip_address=ip_address,
        metadata={
            "conversation_id": conversation.id,
            "message_id": message.id,
            "attachments_count": len(attachments),
        },
    )
    if should_notify_support_team or was_closed:
        notify_support_team_about_ticket(
            text=build_support_team_ticket_notification_text(
                conversation=conversation,
                message=message,
                source_label="Сайт",
                reopened=was_closed,
            )
        )
    return get_support_conversation(user=user)


@transaction.atomic
def create_support_message_from_telegram(
    *,
    user,
    sender_display_name: str,
    text: str,
    attachments: list[IncomingSupportAttachment],
    telegram_user_id: int,
) -> SupportConversation:
    normalized_text = text.strip()
    if not normalized_text and not attachments:
        raise ValidationError({"text": "Добавьте сообщение или прикрепите хотя бы один файл."})

    conversation = get_or_create_support_conversation(user=user)
    should_notify_support_team = conversation.messages.count() == 0
    was_closed = conversation.status == SupportConversation.Status.CLOSED
    message = SupportMessage.objects.create(
        conversation=conversation,
        sender_type=SupportMessage.SenderType.USER,
        sender_user=user,
        sender_display_name=sender_display_name.strip() or "Telegram",
        source=SupportMessage.Source.TELEGRAM_SUPPORT_BOT,
        text=normalized_text,
    )

    for attachment in attachments:
        support_attachment = SupportAttachment(
            message=message,
            file_name=attachment.file_name,
            content_type=attachment.content_type,
            size_bytes=len(attachment.content_bytes),
        )
        support_attachment.file.save(
            attachment.file_name,
            ContentFile(attachment.content_bytes),
            save=False,
        )
        support_attachment.save()

    refresh_support_conversation_state(conversation=conversation, message=message)
    log_user_activity(
        user=user,
        action="support_message_sent",
        description="Пользователь отправил сообщение в поддержку через Telegram.",
        metadata={
            "conversation_id": conversation.id,
            "message_id": message.id,
            "attachments_count": len(attachments),
            "source": SupportMessage.Source.TELEGRAM_SUPPORT_BOT,
            "telegram_user_id": telegram_user_id,
        },
    )
    if should_notify_support_team or was_closed:
        notify_support_team_about_ticket(
            text=build_support_team_ticket_notification_text(
                conversation=conversation,
                message=message,
                source_label="Telegram",
                reopened=was_closed,
            )
        )
    return get_support_conversation(user=user)


@transaction.atomic
def create_support_message_from_admin(
    *,
    admin_user: User,
    conversation: SupportConversation,
    text: str,
    attachments: list | None = None,
) -> SupportMessage:
    admin_attachments = list(attachments or [])
    if not text.strip() and not admin_attachments:
        raise ValidationError({"text": "Ответ администратора не может быть пустым."})

    display_name = admin_user.get_full_name() or admin_user.username or "Администратор"
    message = SupportMessage.objects.create(
        conversation=conversation,
        sender_type=SupportMessage.SenderType.ADMIN,
        sender_user=admin_user,
        sender_display_name=display_name,
        source=SupportMessage.Source.ADMIN,
        text=text.strip(),
    )

    for uploaded_file in admin_attachments:
        SupportAttachment.objects.create(
            message=message,
            file=uploaded_file,
            file_name=uploaded_file.name,
            content_type=getattr(uploaded_file, "content_type", "") or "",
            size_bytes=getattr(uploaded_file, "size", 0) or 0,
        )

    refresh_support_conversation_state(conversation=conversation, message=message)
    deliver_support_message_to_user(conversation=conversation, message=message)
    dispatch_notification(
        event_type="support_message",
        user=conversation.user,
        payload={
            "conversation_id": conversation.id,
            "message_id": message.id,
            "message_preview": (message.text or "").strip()[:280],
        },
    )
    return message


@transaction.atomic
def assign_support_conversation_to_admin(*, conversation: SupportConversation, admin_user: User) -> SupportConversation:
    conversation.assigned_admin = admin_user
    conversation.status = SupportConversation.Status.IN_PROGRESS
    conversation.closed_at = None
    conversation.save(update_fields=["assigned_admin", "status", "closed_at", "updated_at"])
    return conversation


@transaction.atomic
def close_support_conversation(*, conversation: SupportConversation, closed_by: User | None = None) -> SupportConversation:
    if conversation.status == SupportConversation.Status.CLOSED:
        return conversation

    closing_display_name = (
        closed_by.get_full_name() or closed_by.username
        if closed_by is not None
        else "Система поддержки"
    )
    closing_message = SupportMessage.objects.create(
        conversation=conversation,
        sender_type=SupportMessage.SenderType.ADMIN,
        sender_user=closed_by,
        sender_display_name=closing_display_name,
        source=SupportMessage.Source.ADMIN,
        text="Диалог закрыт. Если появятся новые вопросы, вы можете открыть его новым сообщением.",
    )
    refresh_support_conversation_state(conversation=conversation, message=closing_message)
    notify_support_conversation_closed(conversation=conversation)
    conversation.status = SupportConversation.Status.CLOSED
    conversation.closed_at = timezone.now()
    conversation.save(update_fields=["status", "closed_at", "updated_at"])
    return conversation


def build_support_team_ticket_notification_text(
    *,
    conversation: SupportConversation,
    message: SupportMessage,
    source_label: str,
    reopened: bool,
) -> str:
    ticket_state_label = "Переоткрыт тикет" if reopened else "Новый тикет"
    user_label = conversation.user.get_full_name() or conversation.user.username or conversation.user.email
    message_preview = (message.text or "").strip() or "Без текста, только вложения"
    return (
        f"{ticket_state_label} #{conversation.id}\n"
        f"Пользователь: {user_label}\n"
        f"Источник: {source_label}\n"
        f"Сообщение: {message_preview[:300]}"
    )


def deliver_support_message_to_user(*, conversation: SupportConversation, message: SupportMessage) -> None:
    if message.sender_type != SupportMessage.SenderType.ADMIN:
        return

    delivery_channel = get_support_delivery_channel(conversation=conversation)
    if delivery_channel != SupportMessage.Source.TELEGRAM_SUPPORT_BOT:
        return

    telegram_link = get_active_telegram_link(user=conversation.user)
    if telegram_link is None:
        return

    attachments = list(message.attachments.all())
    attachment_names = [attachment.file_name for attachment in attachments]
    attachment_block = ""
    if attachment_names:
        attachment_block = "\nВложения: " + ", ".join(attachment_names)

    message_body = message.text.strip() or "Оператор отправил ответ с вложениями."

    send_telegram_message(
        chat_id=telegram_link.telegram_user_id,
        text=(
            f"Ответ по тикету #{conversation.id}\n"
            f"{message.sender_display_name}: {message_body}"
            f"{attachment_block}"
        ),
    )

    for attachment in attachments:
        attachment.file.open("rb")
        try:
            send_telegram_document(
                chat_id=telegram_link.telegram_user_id,
                file_name=attachment.file_name,
                content_bytes=attachment.file.read(),
            )
        finally:
            attachment.file.close()


def notify_support_conversation_closed(*, conversation: SupportConversation) -> None:
    delivery_channel = get_support_delivery_channel(conversation=conversation)
    if delivery_channel != SupportMessage.Source.TELEGRAM_SUPPORT_BOT:
        return

    telegram_link = get_active_telegram_link(user=conversation.user)
    if telegram_link is None:
        return

    send_telegram_message(
        chat_id=telegram_link.telegram_user_id,
        text=(
            f"Диалог по тикету #{conversation.id} закрыт. "
            "Если появятся новые вопросы, просто напишите в этот чат снова."
        ),
    )


def ensure_support_conversation_admin_access(
    *,
    conversation: SupportConversation,
    admin_user: User,
) -> None:
    if conversation.assigned_admin_id is None:
        return

    if conversation.assigned_admin_id == admin_user.id:
        return

    raise ValidationError(
        {
            "assigned_admin": (
                "Диалог уже закреплен за другим оператором. "
                "Сначала переназначьте его явно."
            )
        }
    )


@transaction.atomic
def reply_to_support_conversation(
    *,
    admin_user: User,
    conversation: SupportConversation,
    text: str,
    attachments: list | None = None,
    assign_to_admin: bool = False,
    close_after_reply: bool = False,
) -> SupportConversation:
    if assign_to_admin or conversation.assigned_admin_id is None:
        assign_support_conversation_to_admin(
            conversation=conversation,
            admin_user=admin_user,
        )
    else:
        ensure_support_conversation_admin_access(
            conversation=conversation,
            admin_user=admin_user,
        )

    create_support_message_from_admin(
        admin_user=admin_user,
        conversation=conversation,
        text=text,
        attachments=attachments,
    )

    if close_after_reply:
        close_support_conversation(
            conversation=conversation,
            closed_by=admin_user,
        )

    return get_or_create_support_conversation(user=conversation.user)
