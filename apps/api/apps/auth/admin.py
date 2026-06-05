from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.sites import NotRegistered
from django.utils import timezone

from apps.activity.models import UserActivity
from apps.profile.models import UserProfile
from apps.subscription.models import Subscription, SubscriptionPayment
from apps.subscription.services import activate_subscription_plan, create_trial_subscription, remove_user_subscription


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


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    can_delete = False
    fields = ("plan_name", "starts_at", "ends_at", "max_devices", "main_url", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    verbose_name_plural = "Текущая подписка"


class SubscriptionPaymentInline(admin.TabularInline):
    model = SubscriptionPayment
    extra = 0
    can_delete = False
    fields = ("created_at", "plan_name", "amount_rub", "status", "provider_status", "paid_at")
    readonly_fields = ("created_at", "plan_name", "amount_rub", "status", "provider_status", "paid_at")
    ordering = ("-created_at", "-id")
    verbose_name_plural = "История платежей"

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
    inlines = (UserProfileInline, SubscriptionInline, SubscriptionPaymentInline, UserActivityInline)
    actions = (
        "grant_trial_subscription",
        "grant_1_month_subscription",
        "grant_3_months_subscription",
        "grant_6_months_subscription",
        "grant_12_months_subscription",
        "remove_subscription_action",
        "revoke_all_devices_action",
    )
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

    @admin.action(description="Выдать триал-подписку")
    def grant_trial_subscription(self, request, queryset):
        updated = 0
        for user in queryset:
            create_trial_subscription(user=user)
            updated += 1

        self.message_user(
            request,
            f"Триал выдан пользователям: {updated}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Выдать подписку 1 месяц")
    def grant_1_month_subscription(self, request, queryset):
        self._grant_plan(request, queryset, "1m", "1 месяц")

    @admin.action(description="Выдать подписку 3 месяца")
    def grant_3_months_subscription(self, request, queryset):
        self._grant_plan(request, queryset, "3m", "3 месяца")

    @admin.action(description="Выдать подписку 6 месяцев")
    def grant_6_months_subscription(self, request, queryset):
        self._grant_plan(request, queryset, "6m", "6 месяцев")

    @admin.action(description="Выдать подписку 12 месяцев")
    def grant_12_months_subscription(self, request, queryset):
        self._grant_plan(request, queryset, "12m", "12 месяцев")

    @admin.action(description="Убрать подписку у выбранных пользователей")
    def remove_subscription_action(self, request, queryset):
        updated = 0
        for user in queryset:
            remove_user_subscription(user=user)
            updated += 1

        self.message_user(
            request,
            f"Подписка убрана у пользователей: {updated}.",
            level=messages.WARNING,
        )

    @admin.action(description="Отозвать все устройства выбранных пользователей")
    def revoke_all_devices_action(self, request, queryset):
        updated = 0
        revoked_at = timezone.now()
        for user in queryset:
            updated += user.devices.filter(revoked_at__isnull=True).update(revoked_at=revoked_at)

        self.message_user(
            request,
            f"Отозвано устройств: {updated}.",
            level=messages.WARNING,
        )

    def _grant_plan(self, request, queryset, plan_code: str, plan_label: str):
        updated = 0
        for user in queryset:
            activate_subscription_plan(user=user, plan_code=plan_code)
            updated += 1

        self.message_user(
            request,
            f"Подписка «{plan_label}» выдана пользователям: {updated}.",
            level=messages.SUCCESS,
        )
