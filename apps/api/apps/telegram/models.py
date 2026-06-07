from django.conf import settings
from django.db import models


class TelegramAccountLink(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_link",
        verbose_name="Пользователь",
    )
    telegram_user_id = models.BigIntegerField("Telegram user id", unique=True)
    telegram_username = models.CharField("Telegram username", max_length=255, blank=True)
    telegram_full_name = models.CharField("Telegram full name", max_length=255, blank=True)
    linked_at = models.DateTimeField("Привязано", auto_now_add=True)
    is_active = models.BooleanField("Активно", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Привязка Telegram"
        verbose_name_plural = "Привязки Telegram"

    def __str__(self) -> str:
        return f"TelegramLink<{self.user_id}:{self.telegram_user_id}>"


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_link_tokens",
        verbose_name="Пользователь",
    )
    token = models.CharField("Токен", max_length=64, unique=True)
    expires_at = models.DateTimeField("Истекает")
    consumed_at = models.DateTimeField("Использован", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Токен привязки Telegram"
        verbose_name_plural = "Токены привязки Telegram"

    def __str__(self) -> str:
        return f"TelegramLinkToken<{self.user_id}>"

