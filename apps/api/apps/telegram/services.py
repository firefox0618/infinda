from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import quote

import time
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.access.services import build_user_access_state
from apps.activity.models import UserActivity
from apps.activity.services import log_user_activity
from apps.devices.models import Device
from apps.devices.services import repair_user_device, resolve_device_computed_status
from apps.notifications.services import dispatch_notification
from apps.provisioning.services import schedule_device_repair, schedule_manual_subscription_sync
from apps.subscription.services import (
    create_subscription_checkout,
    get_latest_pending_subscription_payment,
    get_user_subscription,
    list_subscription_plans,
)

from .bot_client import TelegramBotClient, TelegramBotClientError
from .models import TelegramAccountLink, TelegramLinkToken


logger = logging.getLogger(__name__)


TELEGRAM_LINK_TTL_MINUTES = 15
TELEGRAM_MENU_BUTTON_SUBSCRIPTION = "Подписка"
TELEGRAM_MENU_BUTTON_DEVICES = "Устройства"
TELEGRAM_MENU_BUTTON_PLANS = "Тарифы"
TELEGRAM_MENU_BUTTON_SYNC = "Синхронизация"
TELEGRAM_MENU_BUTTON_SUPPORT = "Поддержка"
TELEGRAM_MENU_BUTTON_MENU = "Меню"
TELEGRAM_MENU_BUTTON_LINK_HELP = "Как привязать Telegram"
TELEGRAM_MAIN_MENU_TEXT = (
    "Команды INFINDA:\n"
    "/menu - показать это меню\n"
    "/subscription - статус подписки и оплаты\n"
    "/devices - список устройств\n"
    "/plans - доступные тарифы\n"
    "/buy <code> - получить ссылку на оплату\n"
    "/sync - запустить синхронизацию доступа\n"
    "/repair <device_id> - восстановить доступ для устройства\n"
    "/support - как написать в поддержку"
)


def get_active_telegram_link(*, user):
    return TelegramAccountLink.objects.filter(user=user, is_active=True).first()


def build_telegram_main_menu_text() -> str:
    return TELEGRAM_MAIN_MENU_TEXT


def build_telegram_linked_reply_keyboard() -> dict:
    return {
        "keyboard": [
            [
                {"text": TELEGRAM_MENU_BUTTON_SUBSCRIPTION},
                {"text": TELEGRAM_MENU_BUTTON_DEVICES},
            ],
            [
                {"text": TELEGRAM_MENU_BUTTON_PLANS},
                {"text": TELEGRAM_MENU_BUTTON_SYNC},
            ],
            [
                {"text": TELEGRAM_MENU_BUTTON_SUPPORT},
                {"text": TELEGRAM_MENU_BUTTON_MENU},
            ],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def build_telegram_unlinked_reply_keyboard() -> dict:
    return {
        "keyboard": [[{"text": TELEGRAM_MENU_BUTTON_LINK_HELP}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def build_telegram_link_help_text() -> str:
    return (
        "Чтобы использовать INFINDA bot как личный кабинет, сначала привяжите Telegram в web-кабинете.\n"
        "Шаги:\n"
        "1. Откройте кабинет INFINDA.\n"
        "2. Перейдите в раздел Telegram.\n"
        "3. Нажмите кнопку привязки и откройте deep-link."
    )


def build_telegram_subscription_summary(*, user) -> str:
    subscription = get_user_subscription(user=user)
    access_state = build_user_access_state(user=user)
    pending_payment = get_latest_pending_subscription_payment(user=user)

    if subscription is None:
        if pending_payment is not None:
            return (
                "Подписка: ожидает оплаты\n"
                f"Тариф: {pending_payment.plan_name}\n"
                f"Сумма: {pending_payment.amount_rub} RUB\n"
                "После подтверждения оплаты доступ активируется автоматически."
            )
        return (
            "Подписка пока не оформлена.\n"
            "Доступные команды:\n"
            "/menu - команды бота\n"
            "/support - помощь оператора"
        )

    route_count = subscription.routes.count()
    lines = [
        f"Подписка: {subscription.plan_name}",
        f"Статус: {access_state['subscription_status']}",
        f"Активна до: {subscription.ends_at:%d.%m.%Y}",
        f"Осталось дней: {subscription.remaining_days}",
        f"Лимит устройств: {access_state['active_device_count']} из {subscription.max_devices}",
        f"Маршрутов: {route_count}",
    ]
    if pending_payment is not None:
        lines.append(
            f"Есть ожидающая оплата: {pending_payment.plan_name} · {pending_payment.amount_rub} RUB"
        )
    if access_state["provisioning_issue_count"] > 0:
        lines.append(
            "Есть provisioning-проблемы. Проверьте устройства в кабинете или напишите в поддержку."
        )
    return "\n".join(lines)


def build_telegram_devices_summary(*, user) -> str:
    devices = list(Device.objects.filter(user=user).order_by("-last_seen", "-created_at")[:10])
    if not devices:
        return "Устройств пока нет. После первого подключения они появятся здесь."

    lines = ["Ваши устройства:"]
    active_count = 0
    for device in devices:
        computed_status = resolve_device_computed_status(device=device)
        if computed_status == Device.Status.ACTIVE:
            active_count += 1
        lines.append(
            f"- #{device.id} {device.resolved_display_name} · {device.resolved_platform} · "
            f"{device.resolved_client} · {computed_status}"
        )
    lines.append(f"Всего показано: {len(devices)}. Активных: {active_count}.")
    return "\n".join(lines)


def build_telegram_support_hint() -> str:
    return (
        "Напишите сообщение прямо в этот чат, и оно попадет в поддержку INFINDA.\n"
        "Можно отправлять текст, фото и документы.\n"
        "Команда /menu покажет остальные действия."
    )


def build_telegram_subscription_plans_text() -> str:
    lines = ["Доступные тарифы:"]
    for plan in list_subscription_plans():
        lines.append(
            f"- {plan['code']}: {plan['title']} · {plan['price_rub']} RUB · "
            f"{plan['max_devices']} устройств"
        )
    lines.append("Для оплаты используйте команду вида: /buy 3m")
    return "\n".join(lines)


def build_telegram_checkout_message(*, user, plan_code: str) -> str:
    payment = create_subscription_checkout(user=user, plan_code=plan_code)
    return (
        f"Ссылка на оплату тарифа {payment.plan_name}:\n"
        f"{payment.checkout_url}\n"
        "После подтверждения оплаты подписка активируется автоматически."
    )


def build_telegram_sync_result(*, user) -> str:
    subscription = get_user_subscription(user=user)
    if subscription is None:
        return "Активной подписки нет. Сначала оформите доступ через /plans и /buy <code>."

    operations = schedule_manual_subscription_sync(subscription=subscription)
    failed_count = len([item for item in operations if item.status == item.Status.FAILED])
    return (
        "Синхронизация доступа запущена.\n"
        f"Операций: {len(operations)}\n"
        f"Ошибок: {failed_count}"
    )


def build_telegram_device_repair_result(*, user, device_id: int) -> str:
    device = repair_user_device(user=user, device_id=device_id)
    subscription = get_user_subscription(user=user)
    operations = schedule_device_repair(
        subscription=subscription,
        device=device,
        reason="telegram-repair-command",
    )
    failed_count = len([item for item in operations if item.status == item.Status.FAILED])
    return (
        f"Восстановление устройства #{device.id} ({device.resolved_display_name}) запущено.\n"
        f"Операций: {len(operations)}\n"
        f"Ошибок: {failed_count}"
    )


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
