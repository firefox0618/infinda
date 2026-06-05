from django.conf import settings
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name="Пользователь",
    )
    plan_name = models.CharField("Тариф", max_length=120)
    starts_at = models.DateField("Дата начала")
    ends_at = models.DateField("Активна до")
    max_devices = models.PositiveSmallIntegerField("Лимит устройств", default=10)
    main_url = models.URLField("Основная ссылка подписки")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self) -> str:
        return f"{self.user.email} — {self.plan_name}"

    @property
    def remaining_days(self) -> int:
        today = timezone.localdate()
        return max((self.ends_at - today).days, 0)


class SubscriptionRoute(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="routes",
        verbose_name="Подписка",
    )
    code = models.CharField("Код страны", max_length=8)
    label = models.CharField("Страна", max_length=64)
    url = models.URLField("Ссылка маршрута")
    position = models.PositiveSmallIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("position", "id")
        unique_together = ("subscription", "code")
        verbose_name = "Маршрут подписки"
        verbose_name_plural = "Маршруты подписки"

    def __str__(self) -> str:
        return f"{self.subscription.user.email} — {self.label}"
