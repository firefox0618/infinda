from django.conf import settings
from django.db import models


class UserActivity(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "Вход"
        LOGOUT = "logout", "Выход"
        PROFILE_UPDATED = "profile_updated", "Обновление профиля"
        DEVICE_REVOKED = "device_revoked", "Отзыв устройства"
        SUPPORT_MESSAGE_SENT = "support_message_sent", "Сообщение в поддержку"
        TELEGRAM_LINKED = "telegram_linked", "Привязка Telegram"
        TELEGRAM_UNLINKED = "telegram_unlinked", "Отвязка Telegram"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="Пользователь",
    )
    action = models.CharField("Действие", max_length=32, choices=Action.choices)
    description = models.CharField("Описание", max_length=255)
    ip_address = models.GenericIPAddressField(
        "IP-адрес",
        protocol="both",
        null=True,
        blank=True,
    )
    metadata = models.JSONField("Метаданные", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Действие пользователя"
        verbose_name_plural = "Действия пользователей"

    def __str__(self) -> str:
        return f"{self.user.email} — {self.get_action_display()}"
