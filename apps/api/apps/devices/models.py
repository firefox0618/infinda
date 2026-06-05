from django.conf import settings
from django.db import models
from django.utils import timezone


class Device(models.Model):
    class Icon(models.TextChoices):
        DESKTOP = "desktop", "Desktop"
        MOBILE = "mobile", "Mobile"
        LAPTOP = "laptop", "Laptop"

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
        verbose_name="Пользователь",
    )
    name = models.CharField("Устройство", max_length=120)
    icon = models.CharField("Иконка", max_length=16, choices=Icon.choices)
    ip_address = models.GenericIPAddressField("IP-адрес", protocol="both")
    last_seen = models.DateTimeField("Последняя активность", default=timezone.now)
    status = models.CharField("Статус", max_length=16, choices=Status.choices)
    platform_name = models.CharField("Платформа", max_length=80)
    client_name = models.CharField("Клиент", max_length=80)
    revoked_at = models.DateTimeField("Отозвано", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("-last_seen", "-created_at")
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"

    def __str__(self) -> str:
        return f"Device<{self.user_id}:{self.name}>"

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None
