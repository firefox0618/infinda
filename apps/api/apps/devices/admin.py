from django.contrib import admin

from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "platform_name", "client_name", "status", "last_seen")
    list_filter = ("status", "icon", "platform_name", "client_name")
    search_fields = ("name", "user__email", "user__username", "ip_address")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("user", "name", "icon", "status"),
            },
        ),
        (
            "Подключение",
            {
                "fields": ("platform_name", "client_name", "ip_address", "last_seen", "revoked_at"),
            },
        ),
        (
            "Служебное",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
