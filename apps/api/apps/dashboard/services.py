from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.devices.models import Device
from apps.activity.models import UserActivity
from apps.subscription.models import Subscription, SubscriptionPayment
from apps.support.models import SupportConversation, SupportMessage


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


def _build_new_tickets():
    return (
        SupportConversation.objects.select_related("user", "assigned_admin")
        .filter(status=SupportConversation.Status.NEW)
        .order_by("-last_message_at", "-updated_at", "-id")[:6]
    )


def _build_unassigned_tickets():
    return (
        SupportConversation.objects.select_related("user")
        .filter(assigned_admin__isnull=True)
        .exclude(status=SupportConversation.Status.CLOSED)
        .order_by("-last_message_at", "-updated_at", "-id")[:6]
    )


def _build_expiring_subscriptions(today):
    return (
        Subscription.objects.select_related("user")
        .filter(ends_at__gte=today, ends_at__lte=today + timedelta(days=7))
        .order_by("ends_at", "id")[:6]
    )


def _build_device_alerts():
    stale_before = timezone.now() - timedelta(days=7)
    return (
        Device.objects.select_related("user")
        .filter(revoked_at__isnull=True)
        .filter(Q(status=Device.Status.STALE) | Q(last_seen__lte=stale_before))
        .order_by("last_seen", "id")[:6]
    )


def _build_quick_links():
    return [
        {
            "label": "Новые тикеты",
            "note": "Открыть очередь новых обращений",
            "url_name": "admin:support_supportconversation_changelist",
            "query": "status__exact=new",
        },
        {
            "label": "Pending платежи",
            "note": "Проверить ожидающие оплаты записи",
            "url_name": "admin:subscription_subscriptionpayment_changelist",
            "query": "status__exact=pending",
        },
        {
            "label": "Истекающие подписки",
            "note": "Открыть подписки с близким окончанием",
            "url_name": "admin:subscription_subscription_changelist",
            "query": "timeline=ending_soon",
        },
        {
            "label": "Без Telegram",
            "note": "Найти пользователей без привязки Telegram",
            "url_name": "admin:auth_user_changelist",
            "query": "telegram_state=unlinked",
        },
        {
            "label": "Проблемные устройства",
            "note": "Проверить offline и давно неактивные устройства",
            "url_name": "admin:devices_device_changelist",
            "query": "attention_state=needs_review",
        },
    ]


def _prepare_quick_links():
    return [dict(link) for link in _build_quick_links()]


def _build_support_events():
    return (
        SupportMessage.objects.select_related("conversation__user", "sender_user")
        .filter(sender_type=SupportMessage.SenderType.ADMIN)
        .order_by("-created_at", "-id")[:6]
    )


def _collect_dashboard_counts(*, today):
    month_start = today.replace(day=1)
    stale_before = timezone.now() - timedelta(days=7)
    User = get_user_model()
    users = User.objects.all()

    current_month_paid = SubscriptionPayment.objects.filter(
        status=SubscriptionPayment.STATUS_PAID,
        paid_at__date__gte=month_start,
    )
    active_subscriptions = Subscription.objects.filter(ends_at__gte=today)
    expired_subscriptions = Subscription.objects.filter(ends_at__lt=today)
    open_tickets = SupportConversation.objects.exclude(status=SupportConversation.Status.CLOSED)
    problem_payments = SubscriptionPayment.objects.filter(
        status__in=(
            SubscriptionPayment.STATUS_PENDING,
            SubscriptionPayment.STATUS_FAILED,
            SubscriptionPayment.STATUS_CANCELED,
        )
    )
    active_devices = Device.objects.filter(revoked_at__isnull=True)
    users_without_telegram = users.filter(telegram_link__isnull=True)

    return {
        "month_start": month_start,
        "current_month_paid": current_month_paid,
        "current_month_paid_total": current_month_paid.aggregate(total=Sum("amount_rub"))["total"] or 0,
        "current_month_paid_count": current_month_paid.count(),
        "active_subscriptions_count": active_subscriptions.count(),
        "expired_subscriptions_count": expired_subscriptions.count(),
        "new_users_count": users.filter(date_joined__date__gte=month_start).count(),
        "users_count": users.count(),
        "open_tickets_count": open_tickets.count(),
        "unassigned_tickets_count": SupportConversation.objects.filter(
            assigned_admin__isnull=True
        )
        .exclude(status=SupportConversation.Status.CLOSED)
        .count(),
        "problem_payments_count": problem_payments.count(),
        "pending_payments_count": SubscriptionPayment.objects.filter(
            status=SubscriptionPayment.STATUS_PENDING
        ).count(),
        "active_devices_count": active_devices.count(),
        "device_alerts": _build_device_alerts(),
        "device_alerts_count": Device.objects.filter(revoked_at__isnull=True)
        .filter(Q(status=Device.Status.STALE) | Q(last_seen__lte=stale_before))
        .count(),
        "new_tickets_count": SupportConversation.objects.filter(
            status=SupportConversation.Status.NEW
        ).count(),
        "expiring_subscriptions": _build_expiring_subscriptions(today),
        "expiring_subscriptions_count": Subscription.objects.filter(
            ends_at__gte=today,
            ends_at__lte=today + timedelta(days=7),
        ).count(),
        "recent_payments": SubscriptionPayment.objects.select_related("user").order_by(
            "-created_at",
            "-id",
        )[:8],
        "recent_activities": UserActivity.objects.select_related("user").order_by(
            "-created_at",
            "-id",
        )[:8],
        "problem_payments": _build_problem_payments(),
        "new_tickets": _build_new_tickets(),
        "unassigned_tickets": _build_unassigned_tickets(),
        "users_without_telegram_count": users_without_telegram.count(),
    }


def _build_dashboard_cards(*, counts):
    return [
        {
            "label": "Оплачено за месяц",
            "value": f"{counts['current_month_paid_total']} ₽",
            "note": f"Успешных платежей: {counts['current_month_paid_count']}",
            "url_name": "admin:subscription_subscriptionpayment_changelist",
            "query": "status__exact=paid",
        },
        {
            "label": "Активные подписки",
            "value": counts["active_subscriptions_count"],
            "note": f"Истекших: {counts['expired_subscriptions_count']}",
            "url_name": "admin:subscription_subscription_changelist",
        },
        {
            "label": "Новые пользователи",
            "value": counts["new_users_count"],
            "note": f"Всего пользователей: {counts['users_count']}",
            "url_name": "admin:auth_user_changelist",
        },
        {
            "label": "Открытые тикеты",
            "value": counts["open_tickets_count"],
            "note": f"Без оператора: {counts['unassigned_tickets_count']}",
            "url_name": "admin:support_supportconversation_changelist",
        },
        {
            "label": "Проблемные платежи",
            "value": counts["problem_payments_count"],
            "note": f"Pending: {counts['pending_payments_count']}",
            "url_name": "admin:subscription_subscriptionpayment_changelist",
        },
        {
            "label": "Активные устройства",
            "value": counts["active_devices_count"],
            "note": f"Требуют проверки: {counts['device_alerts_count']}",
            "url_name": "admin:devices_device_changelist",
        },
    ]


def _build_attention_stats(*, counts):
    return {
        "new_tickets_count": counts["new_tickets_count"],
        "unassigned_tickets_count": counts["unassigned_tickets_count"],
        "problem_payments_count": counts["problem_payments_count"],
        "expiring_subscriptions_count": counts["expiring_subscriptions_count"],
        "device_alerts_count": counts["device_alerts_count"],
        "users_without_telegram_count": counts["users_without_telegram_count"],
    }


def build_admin_dashboard_context():
    today = timezone.localdate()
    counts = _collect_dashboard_counts(today=today)

    return {
        "admin_dashboard_cards": _build_dashboard_cards(counts=counts),
        "admin_dashboard_monthly_report": _build_monthly_report(),
        "admin_dashboard_recent_payments": counts["recent_payments"],
        "admin_dashboard_recent_activities": counts["recent_activities"],
        "admin_dashboard_support_events": _build_support_events(),
        "admin_dashboard_quick_links": _prepare_quick_links(),
        "admin_dashboard_new_tickets": counts["new_tickets"],
        "admin_dashboard_unassigned_tickets": counts["unassigned_tickets"],
        "admin_dashboard_problem_payments": counts["problem_payments"],
        "admin_dashboard_expiring_subscriptions": counts["expiring_subscriptions"],
        "admin_dashboard_device_alerts": counts["device_alerts"],
        "admin_dashboard_attention_stats": _build_attention_stats(counts=counts),
    }
