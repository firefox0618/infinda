from django.db import models
from django.utils import timezone


class ServerLocation(models.Model):
    code = models.CharField("Код", max_length=16, unique=True)
    name = models.CharField("Название", max_length=120)
    region = models.CharField("Регион", max_length=120, blank=True)
    country_code = models.CharField("Код страны", max_length=8, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("name", "id")
        verbose_name = "Локация сервера"
        verbose_name_plural = "Локации серверов"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Server(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DEGRADED = "degraded", "Degraded"
        OFFLINE = "offline", "Offline"
        MAINTENANCE = "maintenance", "Maintenance"

    code = models.CharField("Код", max_length=32, unique=True)
    name = models.CharField("Название", max_length=120)
    location = models.ForeignKey(
        ServerLocation,
        on_delete=models.PROTECT,
        related_name="servers",
        verbose_name="Локация",
    )
    provider = models.CharField("Провайдер", max_length=120)
    hostname = models.CharField("Hostname", max_length=255)
    ip_address = models.GenericIPAddressField("IP-адрес", protocol="both")
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.ACTIVE)
    capacity_units = models.PositiveIntegerField("Общая емкость", default=0)
    used_capacity_units = models.PositiveIntegerField("Использовано емкости", default=0)
    last_heartbeat = models.DateTimeField("Последний heartbeat", default=timezone.now)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("name", "id")
        verbose_name = "Сервер"
        verbose_name_plural = "Серверы"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class ServerStatusSnapshot(models.Model):
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name="status_snapshots",
        verbose_name="Сервер",
    )
    status = models.CharField("Статус", max_length=16, choices=Server.Status.choices)
    latency_ms = models.PositiveIntegerField("Latency, ms", null=True, blank=True)
    active_connections = models.PositiveIntegerField("Активных подключений", default=0)
    error_reason = models.CharField("Причина ошибки", max_length=255, blank=True)
    checked_at = models.DateTimeField("Проверено", default=timezone.now)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("-checked_at", "-id")
        verbose_name = "Снимок статуса сервера"
        verbose_name_plural = "Снимки статусов серверов"
        indexes = [models.Index(fields=("server", "checked_at"))]

    def __str__(self) -> str:
        return f"Snapshot<{self.server_id}:{self.status}>"
