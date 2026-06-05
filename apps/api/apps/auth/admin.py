from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.sites import NotRegistered

from apps.activity.models import UserActivity
from apps.profile.models import UserProfile


User = get_user_model()

try:
    admin.site.unregister(User)
except NotRegistered:
    pass


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False
    autocomplete_fields = ()
    fields = ("telegram_handle", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    verbose_name_plural = "Профиль"


class UserActivityInline(admin.TabularInline):
    model = UserActivity
    extra = 0
    can_delete = False
    fields = ("created_at", "action", "description", "ip_address", "metadata")
    readonly_fields = ("created_at", "action", "description", "ip_address", "metadata")
    ordering = ("-created_at", "-id")
    verbose_name_plural = "Последние действия"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class InfindaUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "full_name",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    search_fields = ("id", "username", "email", "first_name", "last_name")
    inlines = (UserProfileInline, UserActivityInline)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Личные данные", {"fields": ("first_name", "last_name", "email")}),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description="ФИО")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "—"
