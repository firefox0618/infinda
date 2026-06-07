from datetime import timedelta

from django.contrib import admin, messages
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import Subscription, SubscriptionPayment, SubscriptionRoute
from .services import (
    extend_subscription_by_days,
    mark_subscription_payment_canceled,
    mark_subscription_payment_failed,
    mark_subscription_payment_paid,
    remove_user_subscription,
)


class SubscriptionRouteInline(admin.TabularInline):
    model = SubscriptionRoute
    extra = 0
    fields = ("position", "code", "label", "url", "connection_route")
    ordering = ("position", "id")


class SubscriptionTimelineFilter(admin.SimpleListFilter):
    title = "Срок"
    parameter_name = "timeline"

    def lookups(self, request, model_admin):
        return (
            ("ending_soon", "Истекают за 7 дней"),
            ("expired", "Истекли"),
            ("active", "Активные"),
        )

    def queryset(self, request, queryset):
        today = timezone.localdate()
        if self.value() == "ending_soon":
            return queryset.filter(ends_at__gte=today, ends_at__lte=today + timedelta(days=7))
        if self.value() == "expired":
            return queryset.filter(ends_at__lt=today)
        if self.value() == "active":
            return queryset.filter(ends_at__gte=today)
        return queryset


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan_name", "starts_at", "ends_at", "remaining_days", "max_devices")
    list_filter = ("plan_name", SubscriptionTimelineFilter, "ends_at", "max_devices")
    search_fields = ("user__email", "user__username", "plan_name")
    autocomplete_fields = ("user",)
    inlines = [SubscriptionRouteInline]
    actions = (
        "extend_by_7_days",
        "extend_by_30_days",
        "remove_subscription",
    )
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

    @admin.display(description="Осталось дней")
    def remaining_days(self, obj: Subscription):
        return obj.remaining_days

    @admin.action(description="Продлить выбранные подписки на 7 дней")
    def extend_by_7_days(self, request, queryset):
        updated = 0
        for subscription in queryset:
            extend_subscription_by_days(subscription=subscription, days=7)
            updated += 1

        self.message_user(
            request,
            f"Продлено подписок: {updated}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Продлить выбранные подписки на 30 дней")
    def extend_by_30_days(self, request, queryset):
        updated = 0
        for subscription in queryset:
            extend_subscription_by_days(subscription=subscription, days=30)
            updated += 1

        self.message_user(
            request,
            f"Продлено подписок: {updated}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Убрать выбранные подписки")
    def remove_subscription(self, request, queryset):
        affected_users = 0
        for subscription in queryset.select_related("user"):
            remove_user_subscription(user=subscription.user)
            affected_users += 1

        self.message_user(
            request,
            f"Удалено подписок: {affected_users}.",
            level=messages.WARNING,
        )


@admin.register(SubscriptionRoute)
class SubscriptionRouteAdmin(admin.ModelAdmin):
    list_display = ("subscription", "position", "label", "code", "connection_route")
    list_filter = ("code",)
    search_fields = ("subscription__user__email", "label", "code")
    autocomplete_fields = ("subscription",)


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    change_list_template = "admin/subscription/subscriptionpayment/change_list.html"
    list_display = (
        "id",
        "user",
        "plan_name",
        "amount_rub",
        "status",
        "provider_status",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "provider", "payment_method", "provider_status", "paid_at", "created_at")
    search_fields = (
        "user__email",
        "user__username",
        "plan_name",
        "plan_code",
        "external_payment_id",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "paid_at")
    actions = (
        "mark_as_paid_and_activate_subscription",
        "mark_as_canceled",
        "mark_as_failed",
    )
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

    @admin.action(description="Пометить как оплаченные и активировать подписку")
    def mark_as_paid_and_activate_subscription(self, request, queryset):
        updated = 0
        for payment in queryset.select_related("user"):
            mark_subscription_payment_paid(payment=payment)
            updated += 1

        self.message_user(
            request,
            f"Оплаченных платежей обработано: {updated}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Пометить как отмененные")
    def mark_as_canceled(self, request, queryset):
        updated = 0
        for payment in queryset:
            mark_subscription_payment_canceled(payment=payment)
            updated += 1

        self.message_user(
            request,
            f"Отмененных платежей отмечено: {updated}.",
            level=messages.WARNING,
        )

    @admin.action(description="Пометить как ошибочные")
    def mark_as_failed(self, request, queryset):
        updated = 0
        for payment in queryset:
            mark_subscription_payment_failed(payment=payment)
            updated += 1

        self.message_user(
            request,
            f"Ошибочных платежей отмечено: {updated}.",
            level=messages.WARNING,
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        queryset = self.get_queryset(request)
        current_month = timezone.localdate().replace(day=1)
        monthly_paid = queryset.filter(
            status=SubscriptionPayment.STATUS_PAID,
            paid_at__date__gte=current_month,
        )
        monthly_report = (
            queryset.filter(status=SubscriptionPayment.STATUS_PAID, paid_at__isnull=False)
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(
                total_amount=Sum("amount_rub"),
                payments_count=Count("id"),
            )
            .order_by("-month")[:12]
        )
        extra_context["financial_summary"] = {
            "current_month_label": current_month.strftime("%m.%Y"),
            "current_month_total": monthly_paid.aggregate(total=Sum("amount_rub"))["total"] or 0,
            "current_month_payments": monthly_paid.count(),
            "total_paid_amount": queryset.filter(
                status=SubscriptionPayment.STATUS_PAID
            ).aggregate(total=Sum("amount_rub"))["total"] or 0,
            "total_paid_count": queryset.filter(status=SubscriptionPayment.STATUS_PAID).count(),
            "monthly_report": list(monthly_report),
        }
        return super().changelist_view(request, extra_context=extra_context)
