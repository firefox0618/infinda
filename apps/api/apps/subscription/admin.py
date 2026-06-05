from django.contrib import admin

from .models import Subscription, SubscriptionPayment, SubscriptionRoute


class SubscriptionRouteInline(admin.TabularInline):
    model = SubscriptionRoute
    extra = 0
    fields = ("position", "code", "label", "url")
    ordering = ("position", "id")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan_name", "ends_at", "max_devices")
    list_filter = ("plan_name", "ends_at", "max_devices")
    search_fields = ("user__email", "user__username", "plan_name")
    autocomplete_fields = ("user",)
    inlines = [SubscriptionRouteInline]
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("user", "plan_name", "main_url"),
            },
        ),
        (
            "Срок и лимиты",
            {
                "fields": ("starts_at", "ends_at", "max_devices"),
            },
        ),
        (
            "Служебное",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(SubscriptionRoute)
class SubscriptionRouteAdmin(admin.ModelAdmin):
    list_display = ("subscription", "position", "label", "code")
    list_filter = ("code",)
    search_fields = ("subscription__user__email", "label", "code")
    autocomplete_fields = ("subscription",)


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan_name",
        "amount_rub",
        "status",
        "provider_status",
        "created_at",
    )
    list_filter = ("status", "provider", "payment_method", "provider_status")
    search_fields = (
        "user__email",
        "user__username",
        "plan_name",
        "plan_code",
        "external_payment_id",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "paid_at")
    fieldsets = (
        (
            "Пользователь и тариф",
            {
                "fields": (
                    "user",
                    "plan_code",
                    "plan_name",
                    "amount_rub",
                    "duration_days",
                    "max_devices",
                ),
            },
        ),
        (
            "Провайдер",
            {
                "fields": (
                    "provider",
                    "payment_method",
                    "status",
                    "provider_status",
                    "external_payment_id",
                    "checkout_url",
                    "provider_payload",
                ),
            },
        ),
        (
            "Служебное",
            {
                "fields": ("paid_at", "created_at", "updated_at"),
            },
        ),
    )
