from django.contrib import admin

from .models import TelegramAccountLink, TelegramLinkToken


@admin.register(TelegramAccountLink)
class TelegramAccountLinkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "telegram_user_id",
        "telegram_username",
        "telegram_full_name",
        "is_active",
        "linked_at",
    )
    list_filter = ("is_active", "linked_at")
    search_fields = (
        "user__email",
        "user__username",
        "telegram_username",
        "telegram_full_name",
        "telegram_user_id",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("linked_at", "created_at", "updated_at")


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token", "expires_at", "consumed_at", "created_at")
    list_filter = ("expires_at", "consumed_at", "created_at")
    search_fields = ("user__email", "user__username", "token")
    autocomplete_fields = ("user",)
    readonly_fields = ("token", "expires_at", "consumed_at", "created_at", "updated_at")

