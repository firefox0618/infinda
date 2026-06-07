from rest_framework import serializers

from .models import Subscription, SubscriptionHistoryEvent, SubscriptionPayment, SubscriptionRoute
from .services import (
    get_latest_pending_subscription_payment,
    get_subscription_status,
    is_trial_subscription,
    list_subscription_history,
    list_subscription_payments,
)


class SubscriptionRouteSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionRoute
        fields = ("code", "label", "url")

    def get_label(self, obj: SubscriptionRoute) -> str:
        if obj.connection_route_id is not None:
            return obj.connection_route.location.name
        return obj.label

    def get_url(self, obj: SubscriptionRoute) -> str:
        if obj.connection_route_id is not None:
            return obj.connection_route.endpoint_url
        return obj.url


class SubscriptionPaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = (
            "id",
            "plan_code",
            "plan_name",
            "amount_rub",
            "status",
            "created_at",
            "paid_at",
        )


class SubscriptionHistoryEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionHistoryEvent
        fields = (
            "id",
            "event_type",
            "plan_code",
            "plan_name",
            "starts_at",
            "ends_at",
            "created_at",
        )


class SubscriptionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("trial", "active", "expired", "pending_payment"))
    is_trial = serializers.BooleanField()
    plan_name = serializers.CharField()
    main_link = serializers.URLField()
    active_until = serializers.DateField()
    remaining_days = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    countries = SubscriptionRouteSerializer(many=True)
    payment_history = SubscriptionPaymentHistorySerializer(many=True)
    subscription_history = SubscriptionHistoryEventSerializer(many=True)
    pending_payment = SubscriptionPaymentHistorySerializer(allow_null=True)


class EmptySubscriptionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("none", "pending_payment"))
    pending_payment = SubscriptionPaymentHistorySerializer(allow_null=True)


def serialize_subscription(*, subscription: Subscription | None, user=None) -> dict:
    if subscription is None:
        pending_payment = get_latest_pending_subscription_payment(user=user) if user is not None else None
        return EmptySubscriptionSerializer(
            {
                "status": "pending_payment" if pending_payment is not None else "none",
                "pending_payment": pending_payment,
            }
        ).data

    return SubscriptionSerializer(
        {
            "status": get_subscription_status(subscription=subscription, user=subscription.user),
            "is_trial": is_trial_subscription(subscription=subscription),
            "plan_name": subscription.plan_name,
            "main_link": subscription.main_url,
            "active_until": subscription.ends_at,
            "remaining_days": subscription.remaining_days,
            "max_devices": subscription.max_devices,
            "countries": subscription.routes.all(),
            "payment_history": list_subscription_payments(user=subscription.user)[:10],
            "subscription_history": list_subscription_history(user=subscription.user)[:10],
            "pending_payment": get_latest_pending_subscription_payment(user=subscription.user),
        }
    ).data


class SubscriptionPlanSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    duration_days = serializers.IntegerField()
    price_rub = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    description = serializers.CharField()


class SubscriptionCheckoutRequestSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=16)


class SubscriptionCheckoutSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    checkout_url = serializers.URLField()
    status = serializers.CharField()
    provider = serializers.CharField()
    payment_method = serializers.CharField()
    plan_code = serializers.CharField()
