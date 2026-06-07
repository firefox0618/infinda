from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.routing.models import ConnectionRoute


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


class SubscriptionHistoryEvent(models.Model):
    EVENT_TRIAL_STARTED = "trial_started"
    EVENT_ACTIVATED = "activated"
    EVENT_RENEWED = "renewed"

    EVENT_CHOICES = (
        (EVENT_TRIAL_STARTED, "Триал начат"),
        (EVENT_ACTIVATED, "Подписка активирована"),
        (EVENT_RENEWED, "Подписка продлена"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_history_events",
        verbose_name="Пользователь",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="history_events",
        verbose_name="Подписка",
    )
    payment = models.ForeignKey(
        "SubscriptionPayment",
        on_delete=models.SET_NULL,
        related_name="history_events",
        null=True,
        blank=True,
        verbose_name="Платеж",
    )
    event_type = models.CharField("Тип события", max_length=32, choices=EVENT_CHOICES)
    plan_code = models.CharField("Код тарифа", max_length=16, blank=True)
    plan_name = models.CharField("Название тарифа", max_length=120)
    starts_at = models.DateField("Дата начала")
    ends_at = models.DateField("Дата окончания")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Событие подписки"
        verbose_name_plural = "События подписки"

    def __str__(self) -> str:
        return f"SubscriptionHistoryEvent<{self.user_id}:{self.event_type}>"


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
    connection_route = models.ForeignKey(
        ConnectionRoute,
        on_delete=models.PROTECT,
        related_name="subscription_routes",
        null=True,
        blank=True,
        verbose_name="Управляемый маршрут",
    )
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


class SubscriptionPayment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELED = "canceled"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Ожидает оплаты"),
        (STATUS_PAID, "Оплачен"),
        (STATUS_CANCELED, "Отменен"),
        (STATUS_FAILED, "Ошибка"),
    )

    PROVIDER_PLATEGA = "platega"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
        verbose_name="Пользователь",
    )
    plan_code = models.CharField("Код тарифа", max_length=16)
    plan_name = models.CharField("Название тарифа", max_length=120)
    amount_rub = models.PositiveIntegerField("Сумма, RUB")
    duration_days = models.PositiveSmallIntegerField("Длительность, дней")
    max_devices = models.PositiveSmallIntegerField("Лимит устройств")
    provider = models.CharField("Провайдер", max_length=32, default=PROVIDER_PLATEGA)
    payment_method = models.CharField("Метод оплаты", max_length=32, default="sbp")
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    external_payment_id = models.CharField(
        "Внешний ID платежа",
        max_length=128,
        blank=True,
        null=True,
        unique=True,
    )
    checkout_url = models.URLField("Ссылка на оплату", max_length=1000, blank=True)
    provider_status = models.CharField("Статус провайдера", max_length=32, blank=True)
    provider_payload = models.JSONField("Payload провайдера", default=dict, blank=True)
    paid_at = models.DateTimeField("Оплачено", blank=True, null=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Платеж подписки"
        verbose_name_plural = "Платежи подписки"
        indexes = [
            models.Index(fields=("user", "status")),
            models.Index(fields=("provider", "status")),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} {self.user.email} {self.plan_name} {self.status}"
