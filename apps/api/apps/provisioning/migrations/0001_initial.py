from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("devices", "0003_device_client_device_display_name_device_platform_and_more"),
        ("routing", "0001_initial"),
        ("servers", "0001_initial"),
        ("subscription", "0005_subscription_public_token"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ServerProvisioningProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("adapter", models.CharField(choices=[("mock", "Mock"), ("manual", "Manual"), ("xui", "3x-ui / XUI")], default="mock", max_length=16, verbose_name="Адаптер")),
                ("is_enabled", models.BooleanField(default=True, verbose_name="Provisioning включен")),
                ("external_node_key", models.CharField(blank=True, max_length=120, verbose_name="Внешний ключ ноды")),
                ("notes", models.TextField(blank=True, verbose_name="Заметки")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("server", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="provisioning_profile", to="servers.server", verbose_name="Сервер")),
            ],
            options={
                "verbose_name": "Provisioning-профиль сервера",
                "verbose_name_plural": "Provisioning-профили серверов",
            },
        ),
        migrations.CreateModel(
            name="ProvisioningOperation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation_type", models.CharField(choices=[("sync_subscription_access", "Синхронизация доступа подписки"), ("provision_device_access", "Выдача доступа устройству"), ("revoke_device_access", "Отзыв доступа устройства"), ("repair_device_access", "Восстановление доступа устройства")], max_length=64, verbose_name="Операция")),
                ("trigger", models.CharField(choices=[("trial_started", "Создан trial"), ("subscription_activated", "Подписка активирована"), ("device_revoked", "Устройство отозвано"), ("manual_sync", "Ручная синхронизация"), ("repair_requested", "Запрошено восстановление")], max_length=64, verbose_name="Триггер")),
                ("status", models.CharField(choices=[("pending", "Ожидает"), ("succeeded", "Успешно"), ("failed", "Ошибка"), ("skipped", "Пропущено")], default="pending", max_length=16, verbose_name="Статус")),
                ("adapter", models.CharField(blank=True, max_length=16, verbose_name="Адаптер")),
                ("request_payload", models.JSONField(blank=True, default=dict, verbose_name="Payload запроса")),
                ("result_payload", models.JSONField(blank=True, default=dict, verbose_name="Payload результата")),
                ("error_code", models.CharField(blank=True, max_length=64, verbose_name="Код ошибки")),
                ("error_message", models.CharField(blank=True, max_length=255, verbose_name="Текст ошибки")),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="Завершено")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("device", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="provisioning_operations", to="devices.device", verbose_name="Устройство")),
                ("route", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="provisioning_operations", to="routing.connectionroute", verbose_name="Маршрут")),
                ("server", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="provisioning_operations", to="servers.server", verbose_name="Сервер")),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="provisioning_operations", to="subscription.subscription", verbose_name="Подписка")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="provisioning_operations", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Provisioning-операция",
                "verbose_name_plural": "Provisioning-операции",
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(fields=["user", "created_at"], name="provisioning_user_created_idx"),
                    models.Index(fields=["status", "created_at"], name="provisioning_status_created_idx"),
                    models.Index(fields=["operation_type", "created_at"], name="provisioning_type_created_idx"),
                ],
            },
        ),
    ]
