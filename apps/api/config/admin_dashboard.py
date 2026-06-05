from datetime import timedelta
from types import MethodType

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect
from django.utils import timezone

from apps.activity.models import UserActivity
from apps.devices.models import Device
from apps.subscription.models import Subscription, SubscriptionPayment


def _build_quick_links():
    return [
        {
            "label": "Платежи подписки",
            "note": "История оплат, ручная обработка и финансы",
            "url_name": "admin:subscription_subscriptionpayment_changelist",
        },
        {
            "label": "Подписки",
            "note": "Продление, снятие, маршруты и статусы",
            "url_name": "admin:subscription_subscription_changelist",
        },
        {
            "label": "Пользователи",
            "note": "Выдача подписок, отзыв устройств, аудит",
            "url_name": "admin:auth_user_changelist",
        },
        {
            "label": "Устройства",
            "note": "Активные, отозванные и проблемные устройства",
            "url_name": "admin:devices_device_changelist",
        },
        {
            "label": "Журнал действий",
            "note": "Последние входы, обновления и события",
            "url_name": "admin:activity_useractivity_changelist",
        },
        {
            "label": "Профили",
            "note": "Контакты и профильные данные пользователей",
            "url_name": "admin:profile_userprofile_changelist",
        },
    ]


def _build_monthly_report():
    monthly_report = list(
        SubscriptionPayment.objects.filter(
            status=SubscriptionPayment.STATUS_PAID,
            paid_at__isnull=False,
        )
        .annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(
            total_amount=Sum("amount_rub"),
            payments_count=Count("id"),
        )
        .order_by("-month")[:6]
    )

    max_total = max((item["total_amount"] or 0 for item in monthly_report), default=0)
    for item in monthly_report:
        total_amount = item["total_amount"] or 0
        item["bar_width"] = int((total_amount / max_total) * 100) if max_total else 0

    return monthly_report


def _build_problem_payments():
    return (
        SubscriptionPayment.objects.select_related("user")
        .filter(
            status__in=(
                SubscriptionPayment.STATUS_PENDING,
                SubscriptionPayment.STATUS_FAILED,
                SubscriptionPayment.STATUS_CANCELED,
            )
        )
        .order_by("-created_at", "-id")[:6]
    )


def _build_expiring_subscriptions(today):
    return (
        Subscription.objects.select_related("user")
        .filter(ends_at__gte=today, ends_at__lte=today + timedelta(days=7))
        .order_by("ends_at", "id")[:6]
    )


def _build_device_alerts():
    return (
        Device.objects.select_related("user")
        .filter(revoked_at__isnull=True)
        .order_by("last_seen", "id")[:6]
    )


def build_admin_dashboard_context():
    today = timezone.localdate()
    month_start = today.replace(day=1)
    User = get_user_model()

    current_month_paid = SubscriptionPayment.objects.filter(
        status=SubscriptionPayment.STATUS_PAID,
        paid_at__date__gte=month_start,
    )
    recent_payments = (
        SubscriptionPayment.objects.select_related("user")
        .order_by("-created_at", "-id")[:8]
    )
    recent_activities = UserActivity.objects.select_related("user").order_by(
        "-created_at", "-id"
    )[:8]
    active_subscriptions = Subscription.objects.filter(ends_at__gte=today)
    expired_subscriptions = Subscription.objects.filter(ends_at__lt=today)

    return {
        "admin_dashboard_cards": [
            {
                "label": "Оплачено за месяц",
                "value": f"{current_month_paid.aggregate(total=Sum('amount_rub'))['total'] or 0} ₽",
                "note": f"Успешных платежей: {current_month_paid.count()}",
            },
            {
                "label": "Активные подписки",
                "value": active_subscriptions.count(),
                "note": f"Истекших: {expired_subscriptions.count()}",
            },
            {
                "label": "Пользователи",
                "value": User.objects.count(),
                "note": (
                    "Новых за месяц: "
                    f"{User.objects.filter(date_joined__date__gte=month_start).count()}"
                ),
            },
            {
                "label": "Устройства",
                "value": Device.objects.filter(revoked_at__isnull=True).count(),
                "note": (
                    "Отозванных: "
                    f"{Device.objects.filter(revoked_at__isnull=False).count()}"
                ),
            },
            {
                "label": "Платежи в ожидании",
                "value": SubscriptionPayment.objects.filter(
                    status=SubscriptionPayment.STATUS_PENDING
                ).count(),
                "note": (
                    "Ошибочных: "
                    f"{SubscriptionPayment.objects.filter(status=SubscriptionPayment.STATUS_FAILED).count()}"
                ),
            },
            {
                "label": "Последние действия",
                "value": UserActivity.objects.count(),
                "note": "Журнал событий пользователей",
            },
        ],
        "admin_dashboard_monthly_report": _build_monthly_report(),
        "admin_dashboard_recent_payments": recent_payments,
        "admin_dashboard_recent_activities": recent_activities,
        "admin_dashboard_quick_links": _build_quick_links(),
        "admin_dashboard_problem_payments": _build_problem_payments(),
        "admin_dashboard_expiring_subscriptions": _build_expiring_subscriptions(today),
        "admin_dashboard_device_alerts": _build_device_alerts(),
    }


def configure_admin_site(admin_site):
    admin_site.index_template = "admin/index.html"
    original_index = admin_site.index
    original_logout = admin_site.logout

    def custom_index(self, request, extra_context=None):
        merged_context = build_admin_dashboard_context()
        if extra_context:
            merged_context.update(extra_context)

        return original_index(request, extra_context=merged_context)

    def custom_logout(self, request, extra_context=None):
        response = original_logout(request, extra_context=extra_context)

        if response.status_code == 200:
            return redirect("admin:login")

        return response

    admin_site.index = MethodType(custom_index, admin_site)
    admin_site.logout = MethodType(custom_logout, admin_site)
