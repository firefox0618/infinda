from django.contrib import admin, messages
from django.utils import timezone

from .models import Device


class RevocationStatusFilter(admin.SimpleListFilter):
    title = "Состояние записи"
    parameter_name = "revocation_state"

    def lookups(self, request, model_admin):
        return (
            ("active", "Активно"),
            ("revoked", "Отозвано"),
        )

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(revoked_at__isnull=True)
        if self.value() == "revoked":
            return queryset.filter(revoked_at__isnull=False)
        return queryset


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "lifecycle_state",
        "platform_name",
        "client_name",
        "status",
        "last_seen",
        "revoked_at",
    )
    list_filter = ("status", "icon", "platform_name", "client_name", RevocationStatusFilter)
    search_fields = ("id", "name", "user__email", "user__username", "ip_address")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "revoked_at")
    actions = ("revoke_selected_devices",)
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

    @admin.display(description="Жизненный цикл")
    def lifecycle_state(self, obj: Device):
        return "Отозвано" if obj.is_revoked else "Активно"

    @admin.action(description="Отозвать выбранные устройства")
    def revoke_selected_devices(self, request, queryset):
        updated = queryset.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
        self.message_user(
            request,
            f"Отозвано устройств: {updated}.",
            level=messages.WARNING,
        )
