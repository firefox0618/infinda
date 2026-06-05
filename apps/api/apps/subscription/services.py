from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from .models import Subscription, SubscriptionPayment, SubscriptionRoute
from .platega import PlategaClient, PlategaError


TRIAL_SUBSCRIPTION_DAYS = 3
TRIAL_PLAN_NAME = "Триал 3 дня"
TRIAL_MAX_DEVICES = 3
SUBSCRIPTION_STATUS_NONE = "none"
SUBSCRIPTION_STATUS_TRIAL = "trial"
SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_EXPIRED = "expired"
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


def get_subscription_status(*, subscription: Subscription | None) -> str:
    if subscription is None:
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


def build_subscription_main_url(*, user, plan_code: str) -> str:
    return f"https://infinda.com/sub/{plan_code}-{user.pk}"


def ensure_subscription_routes(*, subscription: Subscription, plan_code: str) -> None:
    existing_routes = {
        route.code: route for route in subscription.routes.all()
    }

    for index, (code, label) in enumerate(SUBSCRIPTION_ROUTE_DEFINITIONS, start=1):
        defaults = {
            "label": label,
            "url": f"https://infinda.com/sub/{plan_code}-{subscription.user_id}/{code}",
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
        route.position = defaults["position"]
        route.save(update_fields=["label", "url", "position", "updated_at"])

    subscription.routes.exclude(
        code__in=[code for code, _label in SUBSCRIPTION_ROUTE_DEFINITIONS]
    ).delete()


def create_trial_subscription(*, user):
    subscription, created = Subscription.objects.get_or_create(
        user=user,
        defaults={
            "plan_name": TRIAL_PLAN_NAME,
            "starts_at": timezone.localdate(),
            "ends_at": timezone.localdate() + timedelta(days=TRIAL_SUBSCRIPTION_DAYS),
            "max_devices": TRIAL_MAX_DEVICES,
            "main_url": f"https://infinda.com/sub/trial-{user.pk}",
        },
    )

    if created:
        SubscriptionRoute.objects.bulk_create(
            [
                SubscriptionRoute(
                    subscription=subscription,
                    code=code,
                    label=label,
                    url=f"https://infinda.com/sub/trial-{user.pk}/{code}",
                    position=index,
                )
                for index, (code, label) in enumerate(TRIAL_ROUTE_DEFINITIONS, start=1)
            ]
        )

    return subscription


def activate_subscription_plan(*, user, plan_code: str) -> Subscription:
    plan = get_subscription_plan(plan_code=plan_code)
    subscription = get_user_subscription(user=user)
    today = timezone.localdate()

    if subscription is None:
        subscription = Subscription.objects.create(
            user=user,
            plan_name=plan["title"],
            starts_at=today,
            ends_at=today + timedelta(days=plan["duration_days"]),
            max_devices=plan["max_devices"],
            main_url=build_subscription_main_url(user=user, plan_code=plan_code),
        )
    else:
        renewal_base = subscription.ends_at if subscription.ends_at >= today else today
        subscription.plan_name = plan["title"]
        subscription.starts_at = today
        subscription.ends_at = renewal_base + timedelta(days=plan["duration_days"])
        subscription.max_devices = plan["max_devices"]
        subscription.main_url = build_subscription_main_url(user=user, plan_code=plan_code)
        subscription.save(
            update_fields=[
                "plan_name",
                "starts_at",
                "ends_at",
                "max_devices",
                "main_url",
                "updated_at",
            ]
        )

    ensure_subscription_routes(subscription=subscription, plan_code=plan_code)
    subscription.refresh_from_db()
    return subscription


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
        activate_subscription_plan(user=payment.user, plan_code=payment.plan_code)
        payment.save(
            update_fields=[
                "status",
                "provider_status",
                "paid_at",
                "updated_at",
            ]
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

    payment.provider_status = str(callback_payload.get("status") or "").strip().upper()
    payment.provider_payload = callback_payload

    if payment.provider_status == PlategaClient.STATUS_CONFIRMED:
        if payment.status != SubscriptionPayment.STATUS_PAID:
            payment.status = SubscriptionPayment.STATUS_PAID
            payment.paid_at = timezone.now()
            activate_subscription_plan(user=payment.user, plan_code=payment.plan_code)
    elif payment.provider_status in {
        PlategaClient.STATUS_CANCELED,
        PlategaClient.STATUS_CHARGEBACKED,
    }:
        if payment.status == SubscriptionPayment.STATUS_PENDING:
            payment.status = SubscriptionPayment.STATUS_CANCELED
    elif payment.status == SubscriptionPayment.STATUS_PENDING:
        payment.status = SubscriptionPayment.STATUS_PENDING

    payment.save(
        update_fields=[
            "provider_status",
            "provider_payload",
            "status",
            "paid_at",
            "updated_at",
        ]
    )
    return payment
