from django.utils import timezone

from .models import Notification


def build_notification_message(*, notification: Notification) -> str:
    payload = notification.payload

    if notification.event_type == Notification.EVENT_PAYMENT_PAID:
        return (
            f"Оплата подтверждена: {payload.get('plan_name', 'Подписка')}\n"
            f"Сумма: {payload.get('amount_rub', 0)} RUB\n"
            f"Доступ активен до: {payload.get('active_until', 'не указано')}"
        )

    if notification.event_type == Notification.EVENT_DEVICE_REVOKED:
        reason = payload.get("revoked_reason") or "Причина не указана"
        return (
            f"Устройство отозвано: {payload.get('display_name', 'Устройство')}\n"
            f"{payload.get('platform', '')} · {payload.get('client', '')}\n"
            f"Причина: {reason}"
        )

    if notification.event_type == Notification.EVENT_SUPPORT_MESSAGE:
        return (
            f"Новое сообщение от поддержки\n"
            f"Диалог #{payload.get('conversation_id', '—')}\n"
            f"{payload.get('message_preview', 'Откройте кабинет, чтобы прочитать ответ.')}"
        )

    if notification.event_type == Notification.EVENT_TELEGRAM_LINKED:
        return "Telegram успешно привязан к аккаунту INFINDA."

    if notification.event_type == Notification.EVENT_TELEGRAM_UNLINKED:
        return "Telegram отвязан от аккаунта INFINDA."

    if notification.event_type == Notification.EVENT_SUBSCRIPTION_EXPIRING_SOON:
        return (
            f"Подписка скоро истечет.\n"
            f"Тариф: {payload.get('plan_name', 'Подписка')}\n"
            f"Активна до: {payload.get('active_until', 'не указано')}"
        )

    return "У вас новое уведомление INFINDA."


def mark_notification_sent(*, notification: Notification) -> Notification:
    notification.status = Notification.STATUS_SENT
    notification.sent_at = timezone.now()
    notification.failed_at = None
    notification.error_message = ""
    notification.save(update_fields=["status", "sent_at", "failed_at", "error_message"])
    return notification


def mark_notification_failed(*, notification: Notification, message: str) -> Notification:
    notification.status = Notification.STATUS_FAILED
    notification.failed_at = timezone.now()
    notification.error_message = message[:255]
    notification.save(update_fields=["status", "failed_at", "error_message"])
    return notification


def mark_notification_skipped(*, notification: Notification, message: str) -> Notification:
    notification.status = Notification.STATUS_SKIPPED
    notification.error_message = message[:255]
    notification.save(update_fields=["status", "error_message"])
    return notification


def dispatch_notification(*, event_type: str, user, payload: dict | None = None) -> Notification:
    from apps.telegram.services import get_active_telegram_link, send_telegram_message

    notification = Notification.objects.create(
        user=user,
        event_type=event_type,
        channel=Notification.CHANNEL_TELEGRAM,
        payload=payload or {},
        status=Notification.STATUS_PENDING,
    )

    telegram_link = get_active_telegram_link(user=user)
    if telegram_link is None:
        return mark_notification_skipped(
            notification=notification,
            message="Telegram account is not linked.",
        )

    try:
        send_telegram_message(
            chat_id=telegram_link.telegram_user_id,
            text=build_notification_message(notification=notification),
        )
    except Exception as exc:
        return mark_notification_failed(notification=notification, message=str(exc))

    return mark_notification_sent(notification=notification)
