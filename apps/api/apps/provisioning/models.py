from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.devices.models import Device
from apps.routing.models import ConnectionRoute
from apps.servers.models import Server
from apps.subscription.models import Subscription


class ServerProvisioningProfile(models.Model):
    class Adapter(models.TextChoices):
        MOCK = "mock", "Mock"
        MANUAL = "manual", "Manual"
        XUI = "xui", "3x-ui / XUI"

    server = models.OneToOneField(
        Server,
        on_delete=models.CASCADE,
        related_name="provisioning_profile",
        verbose_name="Сервер",
    )
    adapter = models.CharField(
        "Адаптер",
        max_length=16,
        choices=Adapter.choices,
        default=Adapter.MOCK,
    )
    is_enabled = models.BooleanField("Provisioning включен", default=True)
    external_node_key = models.CharField("Внешний ключ ноды", max_length=120, blank=True)
    panel_base_url = models.URLField("URL панели", blank=True)
    panel_username = models.CharField("Логин панели", max_length=120, blank=True)
    panel_password = models.CharField("Пароль панели", max_length=255, blank=True)
    default_inbound_id = models.PositiveIntegerField("Inbound ID по умолчанию", default=0)
    verify_tls = models.BooleanField("Проверять TLS панели", default=True)
    request_timeout_seconds = models.PositiveSmallIntegerField("Таймаут запросов, сек", default=15)
    notes = models.TextField("Заметки", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Provisioning-профиль сервера"
        verbose_name_plural = "Provisioning-профили серверов"

    def __str__(self) -> str:
        return f"ProvisioningProfile<{self.server.code}:{self.adapter}>"


class ProvisioningOperation(models.Model):
    class OperationType(models.TextChoices):
        SYNC_SUBSCRIPTION_ACCESS = "sync_subscription_access", "Синхронизация доступа подписки"
        PROVISION_DEVICE_ACCESS = "provision_device_access", "Выдача доступа устройству"
        REVOKE_DEVICE_ACCESS = "revoke_device_access", "Отзыв доступа устройства"
        REPAIR_DEVICE_ACCESS = "repair_device_access", "Восстановление доступа устройства"

    class Trigger(models.TextChoices):
        TRIAL_STARTED = "trial_started", "Создан trial"
        SUBSCRIPTION_ACTIVATED = "subscription_activated", "Подписка активирована"
        DEVICE_REVOKED = "device_revoked", "Устройство отозвано"
        MANUAL_SYNC = "manual_sync", "Ручная синхронизация"
        REPAIR_REQUESTED = "repair_requested", "Запрошено восстановление"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        SUCCEEDED = "succeeded", "Успешно"
        FAILED = "failed", "Ошибка"
        SKIPPED = "skipped", "Пропущено"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provisioning_operations",
        verbose_name="Пользователь",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="provisioning_operations",
        verbose_name="Подписка",
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="provisioning_operations",
        verbose_name="Устройство",
        null=True,
        blank=True,
    )
    route = models.ForeignKey(
        ConnectionRoute,
        on_delete=models.CASCADE,
        related_name="provisioning_operations",
        verbose_name="Маршрут",
        null=True,
        blank=True,
    )
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name="provisioning_operations",
        verbose_name="Сервер",
        null=True,
        blank=True,
    )
    operation_type = models.CharField("Операция", max_length=64, choices=OperationType.choices)
    trigger = models.CharField("Триггер", max_length=64, choices=Trigger.choices)
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.PENDING)
    adapter = models.CharField("Адаптер", max_length=16, blank=True)
    request_payload = models.JSONField("Payload запроса", default=dict, blank=True)
    result_payload = models.JSONField("Payload результата", default=dict, blank=True)
    error_code = models.CharField("Код ошибки", max_length=64, blank=True)
    error_message = models.CharField("Текст ошибки", max_length=255, blank=True)
    finished_at = models.DateTimeField("Завершено", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Provisioning-операция"
        verbose_name_plural = "Provisioning-операции"
        indexes = [
            models.Index(fields=("user", "created_at")),
            models.Index(fields=("status", "created_at")),
            models.Index(fields=("operation_type", "created_at")),
        ]

    def __str__(self) -> str:
        return f"ProvisioningOperation<{self.user_id}:{self.operation_type}:{self.status}>"

    def mark_finished(
        self,
        *,
        status: str,
        result_payload: dict | None = None,
        error_code: str = "",
        error_message: str = "",
        adapter: str = "",
    ) -> None:
        self.status = status
        self.result_payload = result_payload or {}
        self.error_code = error_code.strip()
        self.error_message = error_message.strip()
        self.adapter = adapter.strip()
        self.finished_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "result_payload",
                "error_code",
                "error_message",
                "adapter",
                "finished_at",
                "updated_at",
            ]
        )


class ProvisionedDeviceAccess(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        ERROR = "error", "Ошибка"
        REVOKED = "revoked", "Отозван"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provisioned_device_accesses",
        verbose_name="Пользователь",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="provisioned_device_accesses",
        verbose_name="Подписка",
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="provisioned_accesses",
        verbose_name="Устройство",
    )
    route = models.ForeignKey(
        ConnectionRoute,
        on_delete=models.CASCADE,
        related_name="provisioned_accesses",
        verbose_name="Маршрут",
    )
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name="provisioned_accesses",
        verbose_name="Сервер",
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    adapter = models.CharField("Адаптер", max_length=16, blank=True)
    external_client_uuid = models.CharField("Внешний UUID клиента", max_length=64, blank=True)
    external_client_email = models.CharField("Внешний email клиента", max_length=190, blank=True)
    external_client_id = models.CharField("Внешний ID клиента", max_length=120, blank=True)
    inbound_id = models.PositiveIntegerField("Inbound ID", default=0)
    connection_url = models.TextField("Ссылка подключения", blank=True)
    metadata = models.JSONField("Metadata", default=dict, blank=True)
    last_error_code = models.CharField("Последний код ошибки", max_length=64, blank=True)
    last_error_message = models.CharField("Последняя ошибка", max_length=255, blank=True)
    provisioned_at = models.DateTimeField("Выдано", null=True, blank=True)
    last_synced_at = models.DateTimeField("Последняя синхронизация", null=True, blank=True)
    revoked_at = models.DateTimeField("Отозвано", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ("device_id", "route_id", "id")
        verbose_name = "Выданный доступ устройства"
        verbose_name_plural = "Выданные доступы устройств"
        constraints = [
            models.UniqueConstraint(fields=("device", "route"), name="uniq_provisioned_access_device_route")
        ]
        indexes = [
            models.Index(fields=("user", "status")),
            models.Index(fields=("server", "status")),
            models.Index(fields=("subscription", "status")),
        ]

    def __str__(self) -> str:
        return f"ProvisionedDeviceAccess<{self.user_id}:{self.device_id}:{self.route.code}:{self.status}>"
