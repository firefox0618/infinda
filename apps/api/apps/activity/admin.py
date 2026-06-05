from django.contrib import admin

from .models import UserActivity


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "description", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = (
        "user__email",
        "user__username",
        "description",
        "ip_address",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("user", "action", "description", "ip_address", "metadata", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
