from django.apps import AppConfig


class LegacySyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.legacy_sync"
    verbose_name = "Legacy sync"
