from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import quote

import time
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.activity.models import UserActivity
from apps.activity.services import log_user_activity
from apps.notifications.services import dispatch_notification

from .bot_client import TelegramBotClient
from .models import TelegramAccountLink, TelegramLinkToken


logger = logging.getLogger(__name__)


TELEGRAM_LINK_TTL_MINUTES = 15


def get_active_telegram_link(*, user):
    return TelegramAccountLink.objects.filter(user=user, is_active=True).first()


def get_active_telegram_link_by_telegram_user_id(*, telegram_user_id: int):
    return (
        TelegramAccountLink.objects.select_related("user")
        .filter(telegram_user_id=telegram_user_id, is_active=True)
        .first()
    )


def get_pending_telegram_link_token(*, user):
    now = timezone.now()
    return (
        TelegramLinkToken.objects.filter(
            user=user,
            consumed_at__isnull=True,
            expires_at__gt=now,
        )
        .order_by("-created_at")
        .first()
    )


def build_telegram_deep_link(*, token: str, bot_username: str) -> str:
    normalized_username = bot_username.strip().lstrip("@")
    return f"https://t.me/{normalized_username}?start=link_{quote(token)}"


def get_telegram_link_status(*, user, bot_username: str):
    link = get_active_telegram_link(user=user)
    pending_token = get_pending_telegram_link_token(user=user)

    return {
        "link": link,
        "pending_link_expires_at": pending_token.expires_at if pending_token else None,
        "pending_deep_link_url": (
            build_telegram_deep_link(token=pending_token.token, bot_username=bot_username)
            if pending_token
            else None
        ),
    }


@transaction.atomic
def create_telegram_link_token(*, user, bot_username: str) -> TelegramLinkToken:
    now = timezone.now()
    TelegramLinkToken.objects.filter(
        user=user,
        consumed_at__isnull=True,
        expires_at__lte=now,
    ).delete()

    existing_token = get_pending_telegram_link_token(user=user)
    if existing_token:
        return existing_token

    link_token = TelegramLinkToken.objects.create(
        user=user,
        token=token_urlsafe(24),
        expires_at=now + timedelta(minutes=TELEGRAM_LINK_TTL_MINUTES),
    )
    return link_token


@transaction.atomic
def confirm_telegram_link(
    *,
    token: str,
    telegram_user_id: int,
    telegram_username: str = "",
    telegram_full_name: str = "",
) -> TelegramAccountLink:
    now = timezone.now()
    link_token = TelegramLinkToken.objects.select_related("user").filter(token=token).first()

    if link_token is None:
        raise ValidationError({"token": "Токен привязки не найден."})

    if link_token.consumed_at is not None:
        raise ValidationError({"token": "Токен привязки уже использован."})

    if link_token.expires_at <= now:
        raise ValidationError({"token": "Срок действия токена истек."})

    existing_link = TelegramAccountLink.objects.filter(
        telegram_user_id=telegram_user_id,
        is_active=True,
    ).exclude(user=link_token.user).first()
    if existing_link is not None:
        raise ValidationError({"telegram_user_id": "Этот Telegram уже привязан к другому аккаунту."})

    link = _upsert_telegram_account_link(
        user=link_token.user,
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
        telegram_full_name=telegram_full_name,
    )

    link_token.consumed_at = now
    link_token.save(update_fields=["consumed_at", "updated_at"])

    log_user_activity(
        user=link.user,
        action=UserActivity.Action.TELEGRAM_LINKED,
        description="Пользователь привязал Telegram к аккаунту.",
        metadata={
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
        },
    )
    dispatch_notification(
        event_type="telegram_linked",
        user=link.user,
        payload={
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
            "telegram_full_name": telegram_full_name,
        },
    )
    return link


def _upsert_telegram_account_link(
    *,
    user,
    telegram_user_id: int,
    telegram_username: str,
    telegram_full_name: str,
) -> TelegramAccountLink:
    link, created = TelegramAccountLink.objects.get_or_create(
        user=user,
        defaults={
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
            "telegram_full_name": telegram_full_name,
            "is_active": True,
        },
    )
    if created:
        return link

    changed_fields: list[str] = []
    if link.telegram_user_id != telegram_user_id:
        link.telegram_user_id = telegram_user_id
        changed_fields.append("telegram_user_id")
    if link.telegram_username != telegram_username:
        link.telegram_username = telegram_username
        changed_fields.append("telegram_username")
    if link.telegram_full_name != telegram_full_name:
        link.telegram_full_name = telegram_full_name
        changed_fields.append("telegram_full_name")
    if not link.is_active:
        link.is_active = True
        changed_fields.append("is_active")

    if changed_fields:
        link.save(update_fields=changed_fields + ["updated_at"])

    return link


@transaction.atomic
def unlink_telegram_account(*, user) -> None:
    link = TelegramAccountLink.objects.filter(user=user, is_active=True).first()
    if link is None:
        return

    link.is_active = False
    link.save(update_fields=["is_active", "updated_at"])
    log_user_activity(
        user=user,
        action=UserActivity.Action.TELEGRAM_UNLINKED,
        description="Пользователь отвязал Telegram от аккаунта.",
        metadata={
            "telegram_user_id": link.telegram_user_id,
            "telegram_username": link.telegram_username,
        },
    )
    dispatch_notification(
        event_type="telegram_unlinked",
        user=user,
        payload={
            "telegram_user_id": link.telegram_user_id,
            "telegram_username": link.telegram_username,
        },
    )


def build_telegram_bot_client() -> TelegramBotClient:
    token = getattr(settings, "TELEGRAM_MAIN_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_MAIN_BOT_TOKEN is not configured.")

    return TelegramBotClient(
        token=token,
        api_base_url=settings.TELEGRAM_BOT_API_BASE_URL,
        request_timeout_seconds=settings.TELEGRAM_BOT_REQUEST_TIMEOUT_SECONDS,
    )


def send_telegram_message(*, chat_id: int, text: str) -> None:
    client = build_telegram_bot_client()
    client.send_message(chat_id=chat_id, text=text)


def send_telegram_document(
    *,
    chat_id: int,
    file_name: str,
    content_bytes: bytes,
    caption: str | None = None,
) -> None:
    client = build_telegram_bot_client()
    client.send_document(
        chat_id=chat_id,
        file_name=file_name,
        content_bytes=content_bytes,
        caption=caption,
    )


def notify_support_team_about_ticket(*, text: str) -> bool:
    chat_id = _get_support_notifications_chat_id()
    if chat_id is None:
        return False

    send_telegram_message(chat_id=chat_id, text=text)
    return True


def _get_support_notifications_chat_id() -> int | None:
    raw_chat_id = str(getattr(settings, "TELEGRAM_SUPPORT_NOTIFICATIONS_CHAT_ID", "")).strip()
    if not raw_chat_id:
        return None

    return int(raw_chat_id)


def run_telegram_bot_polling() -> None:
    from apps.telegram.bot_runtime import process_telegram_update

    client = build_telegram_bot_client()
    offset = None

    while True:
        try:
            updates = client.get_updates(
                offset=offset,
                timeout_seconds=settings.TELEGRAM_BOT_POLL_TIMEOUT_SECONDS,
            )
            for update in updates:
                process_telegram_update(update=update, client=client)
                offset = update["update_id"] + 1
        except TelegramBotClientError as exc:
            logger.warning("Telegram bot error: %s", exc)
            time.sleep(settings.TELEGRAM_BOT_RETRY_DELAY_SECONDS)
