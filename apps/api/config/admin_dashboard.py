from datetime import timedelta
from types import MethodType

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect
from django.utils import timezone

from apps.activity.models import UserActivity
from apps.devices.models import Device
from apps.support.models import SupportConversation, SupportMessage
from apps.subscription.models import Subscription, SubscriptionPayment


ADMIN_WORKSPACES = (
    {
        "key": "overview",
        "label": "Обзор",
        "note": "Операционный центр, очереди внимания и события",
        "icon": "OV",
        "url_name": "admin:index",
        "match_prefixes": ("/admin/",),
    },
    {
        "key": "support",
        "label": "Support",
        "note": "Тикеты, ответы и назначение операторов",
        "icon": "SP",
        "url_name": "admin:support_supportconversation_changelist",
        "match_prefixes": ("/admin/support/",),
    },
    {
        "key": "users",
        "label": "Пользователи",
        "note": "Аккаунты, Telegram, профиль и аудит",
        "icon": "US",
        "url_name": "admin:auth_user_changelist",
        "match_prefixes": (
            "/admin/auth/",
            "/admin/profile/",
            "/admin/telegram/",
            "/admin/activity/",
            "/admin/authtoken/",
        ),
    },
    {
        "key": "payments",
        "label": "Платежи",
        "note": "Оплаты, pending и ручная обработка",
        "icon": "PY",
        "url_name": "admin:subscription_subscriptionpayment_changelist",
        "match_prefixes": ("/admin/subscription/subscriptionpayment/",),
    },
    {
        "key": "subscriptions",
        "label": "Подписки",
        "note": "Сроки, тарифы, лимиты и маршруты",
        "icon": "SB",
        "url_name": "admin:subscription_subscription_changelist",
        "match_prefixes": (
            "/admin/subscription/subscription/",
            "/admin/subscription/subscriptionroute/",
        ),
    },
    {
        "key": "devices",
        "label": "Устройства",
        "note": "Контроль доступа и отзыв устройств",
        "icon": "DV",
        "url_name": "admin:devices_device_changelist",
        "match_prefixes": ("/admin/devices/",),
    },
)

WORKSPACE_MODEL_PREFIXES = {
    "support": ("/admin/support/",),
    "users": (
        "/admin/auth/",
        "/admin/profile/",
        "/admin/telegram/",
        "/admin/activity/",
        "/admin/authtoken/",
    ),
    "payments": ("/admin/subscription/subscriptionpayment/",),
    "subscriptions": (
        "/admin/subscription/subscription/",
        "/admin/subscription/subscriptionroute/",
    ),
    "devices": ("/admin/devices/",),
}


def _clone_app_entry(app, models):
    cloned_app = dict(app)
    cloned_app["models"] = [dict(model) for model in models]
    return cloned_app


def _filter_models_by_prefixes(app_list, prefixes):
    filtered_apps = []

    for app in app_list:
        matched_models = []
        for model in app.get("models", []):
            admin_url = model.get("admin_url") or ""
            if admin_url.startswith(prefixes):
                matched_models.append(model)

        if matched_models:
            filtered_apps.append(_clone_app_entry(app, matched_models))

    return filtered_apps


def _build_workspace_app_list(app_list, active_workspace):
    if active_workspace == "overview":
        secondary_apps = _filter_models_by_prefixes(
            app_list,
            (
                "/admin/activity/",
                "/admin/profile/",
                "/admin/telegram/",
                "/admin/authtoken/",
            ),
        )
        if secondary_apps:
            return secondary_apps

        return _filter_models_by_prefixes(
            app_list,
            tuple(prefix for prefixes in WORKSPACE_MODEL_PREFIXES.values() for prefix in prefixes),
        )

    return _filter_models_by_prefixes(
        app_list,
        WORKSPACE_MODEL_PREFIXES.get(active_workspace, tuple()),
    )


def _build_workspace_links(active_workspace):
    links = []
    for workspace in ADMIN_WORKSPACES:
        link = dict(workspace)
        link["is_active"] = workspace["key"] == active_workspace
        links.append(link)
    return links


def _resolve_active_workspace(request):
    if request.path == "/admin/" or request.path == "/admin":
        return "overview"

    for workspace in ADMIN_WORKSPACES:
        if workspace["key"] == "overview":
            continue

        if request.path.startswith(workspace["match_prefixes"]):
            return workspace["key"]

    return "overview"


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
    open_tickets = SupportConversation.objects.exclude(status=SupportConversation.Status.CLOSED)
    new_tickets_total = SupportConversation.objects.filter(status=SupportConversation.Status.NEW).count()
    unassigned_tickets_total = (
        SupportConversation.objects.filter(assigned_admin__isnull=True)
        .exclude(status=SupportConversation.Status.CLOSED)
        .count()
    )
    problem_payments = SubscriptionPayment.objects.filter(
        status__in=(
            SubscriptionPayment.STATUS_PENDING,
            SubscriptionPayment.STATUS_FAILED,
            SubscriptionPayment.STATUS_CANCELED,
        )
    )
    active_devices = Device.objects.filter(revoked_at__isnull=True)
    users_without_telegram = User.objects.filter(telegram_link__isnull=True)
    new_tickets = _build_new_tickets()
    unassigned_tickets = _build_unassigned_tickets()
    expiring_subscriptions = _build_expiring_subscriptions(today)
    expiring_subscriptions_total = Subscription.objects.filter(
        ends_at__gte=today,
        ends_at__lte=today + timedelta(days=7),
    ).count()
    device_alerts = _build_device_alerts()
    stale_before = timezone.now() - timedelta(days=7)
    device_alerts_total = (
        Device.objects.filter(revoked_at__isnull=True)
        .filter(Q(status=Device.Status.STALE) | Q(last_seen__lte=stale_before))
        .count()
    )

    return {
        "admin_dashboard_cards": [
            {
                "label": "Оплачено за месяц",
                "value": f"{current_month_paid.aggregate(total=Sum('amount_rub'))['total'] or 0} ₽",
                "note": f"Успешных платежей: {current_month_paid.count()}",
                "url_name": "admin:subscription_subscriptionpayment_changelist",
                "query": "status__exact=paid",
            },
            {
                "label": "Активные подписки",
                "value": active_subscriptions.count(),
                "note": f"Истекших: {expired_subscriptions.count()}",
                "url_name": "admin:subscription_subscription_changelist",
            },
            {
                "label": "Новые пользователи",
                "value": User.objects.filter(date_joined__date__gte=month_start).count(),
                "note": (
                    "Всего пользователей: "
                    f"{User.objects.count()}"
                ),
                "url_name": "admin:auth_user_changelist",
            },
            {
                "label": "Открытые тикеты",
                "value": open_tickets.count(),
                "note": f"Без оператора: {unassigned_tickets_total}",
                "url_name": "admin:support_supportconversation_changelist",
            },
            {
                "label": "Проблемные платежи",
                "value": problem_payments.count(),
                "note": (
                    "Pending: "
                    f"{SubscriptionPayment.objects.filter(status=SubscriptionPayment.STATUS_PENDING).count()}"
                ),
                "url_name": "admin:subscription_subscriptionpayment_changelist",
            },
            {
                "label": "Активные устройства",
                "value": active_devices.count(),
                "note": f"Требуют проверки: {device_alerts_total}",
                "url_name": "admin:devices_device_changelist",
            },
        ],
        "admin_dashboard_monthly_report": _build_monthly_report(),
        "admin_dashboard_recent_payments": recent_payments,
        "admin_dashboard_recent_activities": recent_activities,
        "admin_dashboard_support_events": _build_support_events(),
        "admin_dashboard_quick_links": _prepare_quick_links(),
        "admin_dashboard_new_tickets": new_tickets,
        "admin_dashboard_unassigned_tickets": unassigned_tickets,
        "admin_dashboard_problem_payments": _build_problem_payments(),
        "admin_dashboard_expiring_subscriptions": expiring_subscriptions,
        "admin_dashboard_device_alerts": device_alerts,
        "admin_dashboard_attention_stats": {
            "new_tickets_count": new_tickets_total,
            "unassigned_tickets_count": unassigned_tickets_total,
            "problem_payments_count": problem_payments.count(),
            "expiring_subscriptions_count": expiring_subscriptions_total,
            "device_alerts_count": device_alerts_total,
            "users_without_telegram_count": users_without_telegram.count(),
        },
    }


def configure_admin_site(admin_site):
    admin_site.index_template = "admin/index.html"
    original_index = admin_site.index
    original_logout = admin_site.logout
    original_each_context = admin_site.each_context

    def custom_each_context(self, request):
        context = original_each_context(request)
        active_workspace = _resolve_active_workspace(request)
        context["admin_workspaces"] = _build_workspace_links(active_workspace)
        context["admin_active_workspace"] = active_workspace
        context["admin_workspace_app_list"] = _build_workspace_app_list(
            context.get("available_apps", []),
            active_workspace,
        )
        return context

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

    admin_site.each_context = MethodType(custom_each_context, admin_site)
    admin_site.index = MethodType(custom_index, admin_site)
    admin_site.logout = MethodType(custom_logout, admin_site)
