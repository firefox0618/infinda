from django.conf import settings
from django.db import models


class Notification(models.Model):
    EVENT_PAYMENT_PAID = "payment_paid"
    EVENT_SUBSCRIPTION_EXPIRING_SOON = "subscription_expiring_soon"
    EVENT_DEVICE_REVOKED = "device_revoked"
    EVENT_SUPPORT_MESSAGE = "support_message"
    EVENT_TELEGRAM_LINKED = "telegram_linked"
    EVENT_TELEGRAM_UNLINKED = "telegram_unlinked"

    EVENT_CHOICES = (
        (EVENT_PAYMENT_PAID, "Успешная оплата"),
        (EVENT_SUBSCRIPTION_EXPIRING_SOON, "Подписка скоро истекает"),
        (EVENT_DEVICE_REVOKED, "Устройство отозвано"),
        (EVENT_SUPPORT_MESSAGE, "Новое сообщение поддержки"),
        (EVENT_TELEGRAM_LINKED, "Telegram привязан"),
        (EVENT_TELEGRAM_UNLINKED, "Telegram отвязан"),
    )

    CHANNEL_TELEGRAM = "telegram"
    CHANNEL_CHOICES = ((CHANNEL_TELEGRAM, "Telegram"),)

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_SKIPPED = "skipped"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Ожидает"),
        (STATUS_SENT, "Отправлено"),
        (STATUS_FAILED, "Ошибка"),
        (STATUS_SKIPPED, "Пропущено"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
    )
    event_type = models.CharField("Тип события", max_length=64, choices=EVENT_CHOICES)
    channel = models.CharField("Канал", max_length=32, choices=CHANNEL_CHOICES)
    payload = models.JSONField("Payload", default=dict, blank=True)
    status = models.CharField("Статус доставки", max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.CharField("Текст ошибки", max_length=255, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    sent_at = models.DateTimeField("Отправлено", null=True, blank=True)
    failed_at = models.DateTimeField("Ошибка отправки", null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        indexes = [
            models.Index(fields=("user", "event_type")),
            models.Index(fields=("channel", "status")),
        ]

    def __str__(self) -> str:
        return f"Notification<{self.user_id}:{self.event_type}:{self.channel}>"
