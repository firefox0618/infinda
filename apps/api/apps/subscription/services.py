from datetime import timedelta
from secrets import token_urlsafe

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.activity.models import UserActivity
from apps.activity.services import log_user_activity
from apps.devices.models import Device
from apps.devices.services import PublicDeviceTouchError, touch_public_subscription_device
from apps.notifications.services import dispatch_notification
from apps.provisioning.services import schedule_device_repair
from apps.routing.services import ensure_default_route_catalog, get_connection_route_by_code

from .link_builders import build_public_subscription_page_url
from .models import (
    Subscription,
    SubscriptionHistoryEvent,
    SubscriptionPayment,
    SubscriptionRoute,
)
from .platega import PlategaClient, PlategaError


TRIAL_SUBSCRIPTION_DAYS = 3
TRIAL_PLAN_NAME = "Триал 3 дня"
TRIAL_MAX_DEVICES = 3
SUBSCRIPTION_STATUS_NONE = "none"
SUBSCRIPTION_STATUS_TRIAL = "trial"
SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_EXPIRED = "expired"
SUBSCRIPTION_STATUS_PENDING_PAYMENT = "pending_payment"
TRIAL_ROUTE_DEFINITIONS = (
    ("nl", "Нидерланды"),
    ("de", "Германия"),
    ("pl", "Польша"),
)
SUBSCRIPTION_ROUTE_DEFINITIONS = (
    ("ru", "Россия"),
    ("de", "Германия"),
    ("nl", "Нидерланды"),
    ("pl", "Польша"),
)
SUBSCRIPTION_PLAN_CATALOG = (
    {
        "code": "1m",
        "title": "1 месяц",
        "duration_days": 30,
        "price_rub": 149,
        "max_devices": 3,
        "description": "Быстрый старт на один месяц.",
    },
    {
        "code": "3m",
        "title": "3 месяца",
        "duration_days": 90,
        "price_rub": 399,
        "max_devices": 4,
        "description": "Оптимальный тариф на квартал.",
    },
    {
        "code": "6m",
        "title": "6 месяцев",
        "duration_days": 180,
        "price_rub": 749,
        "max_devices": 5,
        "description": "Долгий доступ с повышенным лимитом устройств.",
    },
    {
        "code": "12m",
        "title": "12 месяцев",
        "duration_days": 365,
        "price_rub": 1390,
        "max_devices": 10,
        "description": "Максимальный доступ на год.",
    },
)


class PaymentProviderUnavailable(APIException):
    status_code = 503
    default_code = "PAYMENT_PROVIDER_UNAVAILABLE"
    default_detail = "Платежный провайдер сейчас недоступен."


class PaymentProviderRequestFailed(APIException):
    status_code = 502
    default_code = "PAYMENT_PROVIDER_ERROR"
    default_detail = "Не удалось создать платеж у провайдера."


def get_user_subscription(*, user):
    return (
        Subscription.objects.prefetch_related("routes")
        .filter(user=user)
        .first()
    )


def is_trial_subscription(*, subscription: Subscription) -> bool:
    return subscription.plan_name == TRIAL_PLAN_NAME


def get_subscription_status(*, subscription: Subscription | None, user=None) -> str:
    resolved_user = user or (subscription.user if subscription is not None else None)
    if subscription is not None and resolved_user is not None and has_pending_subscription_payment(user=resolved_user):
        base_status = (
            SUBSCRIPTION_STATUS_EXPIRED
            if subscription.ends_at < timezone.localdate()
            else SUBSCRIPTION_STATUS_TRIAL
            if is_trial_subscription(subscription=subscription)
            else SUBSCRIPTION_STATUS_ACTIVE
        )
        if base_status in (SUBSCRIPTION_STATUS_EXPIRED,):
            return SUBSCRIPTION_STATUS_PENDING_PAYMENT

    if subscription is None:
        if resolved_user is not None and has_pending_subscription_payment(user=resolved_user):
            return SUBSCRIPTION_STATUS_PENDING_PAYMENT
        return SUBSCRIPTION_STATUS_NONE

    if subscription.ends_at < timezone.localdate():
        return SUBSCRIPTION_STATUS_EXPIRED

    if is_trial_subscription(subscription=subscription):
        return SUBSCRIPTION_STATUS_TRIAL

    return SUBSCRIPTION_STATUS_ACTIVE


def list_subscription_plans() -> tuple[dict, ...]:
    return SUBSCRIPTION_PLAN_CATALOG


def get_subscription_plan(*, plan_code: str) -> dict:
    for plan in SUBSCRIPTION_PLAN_CATALOG:
        if plan["code"] == plan_code:
            return plan

    raise ValidationError({"plan_code": "Неизвестный тариф."})


def get_open_subscription_payment(*, user, plan_code: str) -> SubscriptionPayment | None:
    return (
        SubscriptionPayment.objects.filter(
            user=user,
            plan_code=plan_code,
            provider=SubscriptionPayment.PROVIDER_PLATEGA,
            status=SubscriptionPayment.STATUS_PENDING,
        )
        .exclude(checkout_url="")
        .order_by("-created_at")
        .first()
    )


def get_latest_pending_subscription_payment(*, user) -> SubscriptionPayment | None:
    return (
        SubscriptionPayment.objects.filter(
            user=user,
            status=SubscriptionPayment.STATUS_PENDING,
        )
        .order_by("-created_at")
        .first()
    )


def has_pending_subscription_payment(*, user) -> bool:
    return get_latest_pending_subscription_payment(user=user) is not None


def build_public_subscription_token() -> str:
    return token_urlsafe(24)


def build_public_subscription_url(*, token: str) -> str:
    return build_public_subscription_page_url(token=token)


def create_unique_public_subscription_token() -> str:
    token = build_public_subscription_token()
    while Subscription.objects.filter(public_token=token).exists():
        token = build_public_subscription_token()
    return token


def get_public_subscription_by_token(*, token: str) -> Subscription | None:
    return (
        Subscription.objects.prefetch_related("routes")
        .select_related("user")
        .filter(public_token=token)
        .first()
    )


def resolve_subscription_device_by_request_ip(
    *,
    subscription: Subscription,
    request_ip: str | None,
    request_device_key: str | None = None,
) -> Device | None:
    if request_device_key:
        matched_by_key = (
            Device.objects.filter(
                user=subscription.user,
                revoked_at__isnull=True,
                public_device_key=request_device_key,
            )
            .order_by("-last_seen", "-created_at")
            .first()
        )
        if matched_by_key is not None:
            return matched_by_key
    if not request_ip:
        return None
    return (
        Device.objects.filter(
            user=subscription.user,
            revoked_at__isnull=True,
            ip_address=request_ip,
        )
        .order_by("-last_seen", "-created_at")
        .first()
    )


def build_subscription_route_access_snapshot(
    *,
    subscription: Subscription,
    request_ip: str | None = None,
    request_device_key: str | None = None,
) -> dict:
    from apps.provisioning.models import ProvisionedDeviceAccess

    resolved_device = resolve_subscription_device_by_request_ip(
        subscription=subscription,
        request_ip=request_ip,
        request_device_key=request_device_key,
    )
    route_items = list(
        subscription.routes.select_related("connection_route__location", "connection_route__server")
        .order_by("position", "id")
    )
    binding_by_route_id: dict[int, ProvisionedDeviceAccess] = {}
    if resolved_device is not None:
        active_bindings = (
            ProvisionedDeviceAccess.objects.select_related("route")
            .filter(
                subscription=subscription,
                device=resolved_device,
                status=ProvisionedDeviceAccess.Status.ACTIVE,
                revoked_at__isnull=True,
            )
            .exclude(connection_url="")
            .order_by("route_id", "-last_synced_at", "-id")
        )
        for binding in active_bindings:
            binding_by_route_id.setdefault(binding.route_id, binding)

    routes_payload: list[dict] = []
    provisioned_route_count = 0
    for route in route_items:
        binding = (
            binding_by_route_id.get(route.connection_route_id)
            if route.connection_route_id is not None
            else None
        )
        if binding is not None and binding.connection_url:
            resolved_url = binding.connection_url
            is_provisioned = True
            provisioned_route_count += 1
        elif route.connection_route_id is not None:
            resolved_url = route.connection_route.endpoint_url
            is_provisioned = False
        else:
            resolved_url = route.url
            is_provisioned = False

        routes_payload.append(
            {
                "code": route.code,
                "label": route.connection_route.location.name if route.connection_route_id is not None else route.label,
                "url": resolved_url,
                "is_provisioned": is_provisioned,
            }
        )

    return {
        "resolved_device": resolved_device,
        "routes": routes_payload,
        "uses_provisioned_access": provisioned_route_count > 0,
        "provisioned_route_count": provisioned_route_count,
    }


def build_public_subscription_feed(
    *,
    subscription: Subscription,
    request_ip: str | None = None,
    request_device_key: str | None = None,
) -> str:
    snapshot = build_subscription_route_access_snapshot(
        subscription=subscription,
        request_ip=request_ip,
        request_device_key=request_device_key,
    )
    route_urls = [route["url"] for route in snapshot["routes"]]

    return "\n".join(route_urls) + ("\n" if route_urls else "")


def touch_public_subscription(
    *,
    subscription: Subscription,
    request_ip: str | None,
    request_device_key: str | None,
    device_name: str = "",
    platform_name: str = "",
    client_name: str = "",
    icon: str = "",
    user_agent: str = "",
) -> dict:
    subscription_status = get_subscription_status(subscription=subscription, user=subscription.user)
    if subscription_status not in {SUBSCRIPTION_STATUS_TRIAL, SUBSCRIPTION_STATUS_ACTIVE}:
        raise PublicDeviceTouchError(
            code="SUBSCRIPTION_INACTIVE",
            message="Subscription is not active for device binding.",
            details={"status": subscription_status},
        )

    device, created = touch_public_subscription_device(
        subscription=subscription,
        request_ip=request_ip,
        device_key=request_device_key or "",
        device_name=device_name,
        platform_name=platform_name,
        client_name=client_name,
        icon=icon,
    )
    operations = schedule_device_repair(
        subscription=subscription,
        device=device,
        reason="public-subscription-touch",
    )
    failed_operation_count = len(
        [item for item in operations if item.status == item.Status.FAILED]
    )
    log_user_activity(
        user=subscription.user,
        action=UserActivity.Action.PUBLIC_SUBSCRIPTION_TOUCHED,
        description=f"Публичная страница подписки привязала устройство {device.name}.",
        ip_address=request_ip,
        metadata={
            "subscription_id": subscription.id,
            "public_token": subscription.public_token,
            "device_id": device.id,
            "device_name": device.resolved_display_name,
            "device_created": created,
            "device_key_present": bool(request_device_key),
            "scheduled_operation_count": len(operations),
            "failed_operation_count": failed_operation_count,
            "user_agent": user_agent,
        },
    )
    return {
        "ok": True,
        "created": created,
        "scheduled_operation_count": len(operations),
        "failed_operation_count": failed_operation_count,
        "device": {
            "id": device.id,
            "display_name": device.resolved_display_name,
            "platform": device.resolved_platform,
            "client": device.resolved_client,
            "ip": device.ip_address,
        },
    }


def ensure_subscription_routes(*, subscription: Subscription, plan_code: str) -> None:
    ensure_default_route_catalog()
    existing_routes = {
        route.code: route for route in subscription.routes.all()
    }

    for index, (code, label) in enumerate(SUBSCRIPTION_ROUTE_DEFINITIONS, start=1):
        connection_route = get_connection_route_by_code(code=code)
        defaults = {
            "label": connection_route.location.name or label,
            "url": connection_route.endpoint_url,
            "connection_route": connection_route,
            "position": index,
        }
        route = existing_routes.get(code)
        if route is None:
            SubscriptionRoute.objects.create(
                subscription=subscription,
                code=code,
                **defaults,
            )
            continue

        route.label = defaults["label"]
        route.url = defaults["url"]
        route.connection_route = defaults["connection_route"]
        route.position = defaults["position"]
        route.save(update_fields=["label", "url", "connection_route", "position", "updated_at"])

    subscription.routes.exclude(
        code__in=[code for code, _label in SUBSCRIPTION_ROUTE_DEFINITIONS]
    ).delete()


def create_trial_subscription(*, user):
    ensure_default_route_catalog()
    public_token = create_unique_public_subscription_token()
    subscription, created = Subscription.objects.get_or_create(
        user=user,
        defaults={
            "plan_name": TRIAL_PLAN_NAME,
            "starts_at": timezone.localdate(),
            "ends_at": timezone.localdate() + timedelta(days=TRIAL_SUBSCRIPTION_DAYS),
            "max_devices": TRIAL_MAX_DEVICES,
            "public_token": public_token,
            "main_url": build_public_subscription_url(token=public_token),
        },
    )

    if created:
        SubscriptionRoute.objects.bulk_create(
            [
                SubscriptionRoute(
                    subscription=subscription,
                    code=code,
                    label=get_connection_route_by_code(code=code).location.name or label,
                    url=get_connection_route_by_code(code=code).endpoint_url,
                    connection_route=get_connection_route_by_code(code=code),
                    position=index,
                )
                for index, (code, label) in enumerate(TRIAL_ROUTE_DEFINITIONS, start=1)
            ]
        )
        create_subscription_history_event(
            user=user,
            subscription=subscription,
            event_type=SubscriptionHistoryEvent.EVENT_TRIAL_STARTED,
            plan_code="trial",
            plan_name=subscription.plan_name,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
        )
        from apps.provisioning.models import ProvisioningOperation
        from apps.provisioning.services import schedule_subscription_sync

        schedule_subscription_sync(
            subscription=subscription,
            trigger=ProvisioningOperation.Trigger.TRIAL_STARTED,
        )

    return subscription


def activate_subscription_plan(*, user, plan_code: str) -> Subscription:
    plan = get_subscription_plan(plan_code=plan_code)
    subscription = get_user_subscription(user=user)
    today = timezone.localdate()

    previous_ends_at = subscription.ends_at if subscription is not None else None
    if subscription is None:
        public_token = create_unique_public_subscription_token()
        subscription = Subscription.objects.create(
            user=user,
            plan_name=plan["title"],
            starts_at=today,
            ends_at=today + timedelta(days=plan["duration_days"]),
            max_devices=plan["max_devices"],
            public_token=public_token,
            main_url=build_public_subscription_url(token=public_token),
        )
    else:
        renewal_base = subscription.ends_at if subscription.ends_at >= today else today
        subscription.plan_name = plan["title"]
        subscription.starts_at = today
        subscription.ends_at = renewal_base + timedelta(days=plan["duration_days"])
        subscription.max_devices = plan["max_devices"]
        if not subscription.public_token:
            subscription.public_token = create_unique_public_subscription_token()
        subscription.main_url = build_public_subscription_url(token=subscription.public_token)
        subscription.save(
            update_fields=[
                "plan_name",
                "starts_at",
                "ends_at",
                "max_devices",
                "public_token",
                "main_url",
                "updated_at",
            ]
        )

    ensure_subscription_routes(subscription=subscription, plan_code=plan_code)
    subscription.refresh_from_db()
    from apps.provisioning.models import ProvisioningOperation
    from apps.provisioning.services import schedule_subscription_sync

    schedule_subscription_sync(
        subscription=subscription,
        trigger=ProvisioningOperation.Trigger.SUBSCRIPTION_ACTIVATED,
    )
    return subscription


def create_subscription_history_event(
    *,
    user,
    subscription: Subscription,
    event_type: str,
    plan_code: str,
    plan_name: str,
    starts_at,
    ends_at,
    payment: SubscriptionPayment | None = None,
) -> SubscriptionHistoryEvent:
    return SubscriptionHistoryEvent.objects.create(
        user=user,
        subscription=subscription,
        payment=payment,
        event_type=event_type,
        plan_code=plan_code,
        plan_name=plan_name,
        starts_at=starts_at,
        ends_at=ends_at,
    )


@transaction.atomic
def extend_subscription_by_days(*, subscription: Subscription, days: int) -> Subscription:
    if days <= 0:
        raise ValidationError({"days": "Количество дней должно быть больше нуля."})

    today = timezone.localdate()
    renewal_base = subscription.ends_at if subscription.ends_at >= today else today
    subscription.ends_at = renewal_base + timedelta(days=days)
    subscription.save(update_fields=["ends_at", "updated_at"])
    return subscription


@transaction.atomic
def remove_user_subscription(*, user) -> None:
    Subscription.objects.filter(user=user).delete()


@transaction.atomic
def mark_subscription_payment_paid(*, payment: SubscriptionPayment) -> SubscriptionPayment:
    if payment.status != SubscriptionPayment.STATUS_PAID:
        payment.status = SubscriptionPayment.STATUS_PAID
        payment.provider_status = PlategaClient.STATUS_CONFIRMED
        payment.paid_at = timezone.now()
        subscription = activate_subscription_plan(user=payment.user, plan_code=payment.plan_code)
        payment.save(
            update_fields=[
                "status",
                "provider_status",
                "paid_at",
                "updated_at",
            ]
        )
        create_subscription_history_event(
            user=payment.user,
            subscription=subscription,
            payment=payment,
            event_type=(
                SubscriptionHistoryEvent.EVENT_RENEWED
                if SubscriptionHistoryEvent.objects.filter(
                    user=payment.user,
                    payment__isnull=False,
                ).exclude(payment=payment).exists()
                else SubscriptionHistoryEvent.EVENT_ACTIVATED
            ),
            plan_code=payment.plan_code,
            plan_name=payment.plan_name,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
        )
        dispatch_notification(
            event_type="payment_paid",
            user=payment.user,
            payload={
                "payment_id": payment.id,
                "plan_name": payment.plan_name,
                "amount_rub": payment.amount_rub,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                "active_until": subscription.ends_at.isoformat(),
            },
        )

    return payment


def mark_subscription_payment_canceled(*, payment: SubscriptionPayment) -> SubscriptionPayment:
    payment.status = SubscriptionPayment.STATUS_CANCELED
    if not payment.provider_status:
        payment.provider_status = PlategaClient.STATUS_CANCELED
    payment.save(update_fields=["status", "provider_status", "updated_at"])
    return payment


def mark_subscription_payment_failed(*, payment: SubscriptionPayment) -> SubscriptionPayment:
    payment.status = SubscriptionPayment.STATUS_FAILED
    payment.save(update_fields=["status", "updated_at"])
    return payment


def list_subscription_history(*, user):
    return SubscriptionHistoryEvent.objects.filter(user=user).order_by("-created_at", "-id")


def list_subscription_payments(*, user):
    return SubscriptionPayment.objects.filter(user=user).order_by("-created_at", "-id")


def _build_payment_payload(*, payment: SubscriptionPayment) -> dict:
    return {
        "type": "subscription",
        "payment_id": payment.id,
        "user_id": payment.user_id,
        "plan_code": payment.plan_code,
    }


def create_subscription_checkout(*, user, plan_code: str) -> SubscriptionPayment:
    existing_payment = get_open_subscription_payment(user=user, plan_code=plan_code)
    if existing_payment is not None:
        return existing_payment

    plan = get_subscription_plan(plan_code=plan_code)
    payment = SubscriptionPayment.objects.create(
        user=user,
        plan_code=plan["code"],
        plan_name=plan["title"],
        amount_rub=plan["price_rub"],
        duration_days=plan["duration_days"],
        max_devices=plan["max_devices"],
        provider=SubscriptionPayment.PROVIDER_PLATEGA,
        payment_method="sbp",
        status=SubscriptionPayment.STATUS_PENDING,
    )
    client = PlategaClient()
    if not client.configured:
        raise PaymentProviderUnavailable()

    try:
        provider_payment = client.create_payment(
            amount_rub=payment.amount_rub,
            description=f"INFINDA — {payment.plan_name}",
            payload=_build_payment_payload(payment=payment),
            return_url=getattr(settings, "PLATEGA_RETURN_URL", None),
            failed_url=getattr(settings, "PLATEGA_FAILED_URL", None),
        )
    except PlategaError as exc:
        payment.status = SubscriptionPayment.STATUS_FAILED
        payment.provider_payload = {"error": str(exc)}
        payment.save(update_fields=["status", "provider_payload", "updated_at"])
        raise PaymentProviderRequestFailed(str(exc)) from exc

    payment.external_payment_id = provider_payment.transaction_id
    payment.checkout_url = provider_payment.checkout_url
    payment.provider_status = provider_payment.status
    payment.provider_payload = provider_payment.raw
    payment.save(
        update_fields=[
            "external_payment_id",
            "checkout_url",
            "provider_status",
            "provider_payload",
            "updated_at",
        ]
    )
    return payment


@transaction.atomic
def confirm_subscription_payment_from_platega(
    *,
    callback_payload: dict,
    parsed_payload: dict | None = None,
) -> SubscriptionPayment:
    transaction_id = str(callback_payload.get("id") or "").strip()
    if not transaction_id:
        raise ValidationError({"id": "Пустой transaction id."})

    payment = (
        SubscriptionPayment.objects.select_for_update()
        .select_related("user")
        .filter(external_payment_id=transaction_id)
        .first()
    )
    if payment is None:
        raise ValidationError({"id": "Платеж не найден."})

    if parsed_payload is not None:
        payload_payment_id = parsed_payload.get("payment_id")
        payload_user_id = parsed_payload.get("user_id")
        payload_plan_code = parsed_payload.get("plan_code")
        if payload_payment_id is not None and int(payload_payment_id) != payment.id:
            raise ValidationError({"payment_id": "ID платежа не совпадает."})
        if payload_user_id is not None and int(payload_user_id) != payment.user_id:
            raise ValidationError({"user_id": "Пользователь платежа не совпадает."})
        if payload_plan_code is not None and str(payload_plan_code) != payment.plan_code:
            raise ValidationError({"plan_code": "Код тарифа не совпадает."})

    provider_status = str(callback_payload.get("status") or "").strip().upper()
    payment.provider_status = provider_status
    payment.provider_payload = callback_payload
    payment.save(
        update_fields=[
            "provider_status",
            "provider_payload",
            "updated_at",
        ]
    )

    if provider_status == PlategaClient.STATUS_CONFIRMED:
        return mark_subscription_payment_paid(payment=payment)

    if provider_status in {
        PlategaClient.STATUS_CANCELED,
        PlategaClient.STATUS_CHARGEBACKED,
    } and payment.status == SubscriptionPayment.STATUS_PENDING:
        return mark_subscription_payment_canceled(payment=payment)

    return payment
