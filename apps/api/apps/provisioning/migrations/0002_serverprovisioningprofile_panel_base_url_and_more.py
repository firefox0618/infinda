from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("provisioning", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="serverprovisioningprofile",
            name="default_inbound_id",
            field=models.PositiveIntegerField(default=0, verbose_name="Inbound ID по умолчанию"),
        ),
        migrations.AddField(
            model_name="serverprovisioningprofile",
            name="panel_base_url",
            field=models.URLField(blank=True, verbose_name="URL панели"),
        ),
        migrations.AddField(
            model_name="serverprovisioningprofile",
            name="panel_password",
            field=models.CharField(blank=True, max_length=255, verbose_name="Пароль панели"),
        ),
        migrations.AddField(
            model_name="serverprovisioningprofile",
            name="panel_username",
            field=models.CharField(blank=True, max_length=120, verbose_name="Логин панели"),
        ),
        migrations.AddField(
            model_name="serverprovisioningprofile",
            name="request_timeout_seconds",
            field=models.PositiveSmallIntegerField(default=15, verbose_name="Таймаут запросов, сек"),
        ),
        migrations.AddField(
            model_name="serverprovisioningprofile",
            name="verify_tls",
            field=models.BooleanField(default=True, verbose_name="Проверять TLS панели"),
        ),
    ]
