from types import MethodType

from django.shortcuts import redirect

from apps.dashboard.services import build_admin_dashboard_context


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


def _get_overview_secondary_prefixes():
    return (
        "/admin/activity/",
        "/admin/profile/",
        "/admin/telegram/",
        "/admin/authtoken/",
    )


def _get_all_workspace_prefixes():
    return tuple(prefix for prefixes in WORKSPACE_MODEL_PREFIXES.values() for prefix in prefixes)


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


def _collect_secondary_overview_apps(app_list):
    return _filter_models_by_prefixes(app_list, _get_overview_secondary_prefixes())


def _build_workspace_app_list(app_list, active_workspace):
    if active_workspace == "overview":
        secondary_apps = _collect_secondary_overview_apps(app_list)
        if secondary_apps:
            return secondary_apps

        return _filter_models_by_prefixes(app_list, _get_all_workspace_prefixes())

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


def _build_admin_index_context(*, extra_context=None):
    context = build_admin_dashboard_context()
    if extra_context:
        context.update(extra_context)
    return context


def _redirect_logout_response(response):
    if response.status_code == 200:
        return redirect("admin:login")
    return response


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
        return original_index(request, extra_context=_build_admin_index_context(extra_context=extra_context))

    def custom_logout(self, request, extra_context=None):
        response = original_logout(request, extra_context=extra_context)
        return _redirect_logout_response(response)

    admin_site.each_context = MethodType(custom_each_context, admin_site)
    admin_site.index = MethodType(custom_index, admin_site)
    admin_site.logout = MethodType(custom_logout, admin_site)
