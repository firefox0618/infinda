import os
import secrets

from django.db import migrations, models


def _build_public_subscription_url(token: str) -> str:
    base_url = os.getenv("PUBLIC_WEB_BASE_URL", "http://localhost:3000").rstrip("/")
    return f"{base_url}/sub/{token}"


def backfill_subscription_public_token(apps, schema_editor):
    Subscription = apps.get_model("subscription", "Subscription")

    for subscription in Subscription.objects.all().iterator():
        token = secrets.token_urlsafe(24)
        while Subscription.objects.filter(public_token=token).exists():
            token = secrets.token_urlsafe(24)

        subscription.public_token = token
        subscription.main_url = _build_public_subscription_url(token)
        subscription.save(update_fields=["public_token", "main_url", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("subscription", "0004_subscriptionroute_connection_route"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="public_token",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
                unique=True,
                verbose_name="Публичный токен",
            ),
        ),
        migrations.RunPython(backfill_subscription_public_token, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="subscription",
            name="public_token",
            field=models.CharField(max_length=64, unique=True, verbose_name="Публичный токен"),
        ),
    ]
