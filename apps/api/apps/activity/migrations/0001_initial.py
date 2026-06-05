from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("login", "Вход"), ("logout", "Выход"), ("profile_updated", "Обновление профиля"), ("device_revoked", "Отзыв устройства")], max_length=32, verbose_name="Действие")),
                ("description", models.CharField(max_length=255, verbose_name="Описание")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True, protocol="both", verbose_name="IP-адрес")),
                ("metadata", models.JSONField(blank=True, default=dict, verbose_name="Метаданные")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="activities", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Действие пользователя",
                "verbose_name_plural": "Действия пользователей",
                "ordering": ("-created_at", "-id"),
            },
        ),
    ]
