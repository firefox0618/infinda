from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_handle", "updated_at")
    search_fields = ("user__email", "user__username", "telegram_handle")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("user", "telegram_handle"),
            },
        ),
        (
            "Служебное",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
