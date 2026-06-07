from django.db import models

from apps.servers.models import Server


class ProductLocation(models.Model):
    code = models.CharField("Код", max_length=16, unique=True)
    name = models.CharField("Название", max_length=120)
    sort_order = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("sort_order", "name", "id")
        verbose_name = "Продуктовая локация"
        verbose_name_plural = "Продуктовые локации"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class ConnectionRoute(models.Model):
    PROTOCOL_OUTLINE = "outline"

    code = models.CharField("Код", max_length=32, unique=True)
    name = models.CharField("Название", max_length=120)
    location = models.ForeignKey(
        ProductLocation,
        on_delete=models.PROTECT,
        related_name="routes",
        verbose_name="Локация",
    )
    server = models.ForeignKey(
        Server,
        on_delete=models.PROTECT,
        related_name="routes",
        verbose_name="Сервер",
    )
    protocol = models.CharField("Протокол", max_length=32, default=PROTOCOL_OUTLINE)
    endpoint_url = models.URLField("Endpoint URL")
    is_active = models.BooleanField("Активно", default=True)
    priority = models.PositiveSmallIntegerField("Приоритет", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("priority", "name", "id")
        verbose_name = "Маршрут подключения"
        verbose_name_plural = "Маршруты подключения"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
