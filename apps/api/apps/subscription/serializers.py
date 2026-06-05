from rest_framework import serializers

from .models import Subscription, SubscriptionRoute
from .services import get_subscription_status, is_trial_subscription


class SubscriptionRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionRoute
        fields = ("code", "label", "url")


class SubscriptionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("trial", "active", "expired"))
    is_trial = serializers.BooleanField()
    plan_name = serializers.CharField()
    main_link = serializers.URLField()
    active_until = serializers.DateField()
    remaining_days = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    countries = SubscriptionRouteSerializer(many=True)


class EmptySubscriptionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("none",))


def serialize_subscription(*, subscription: Subscription | None) -> dict:
    if subscription is None:
        return EmptySubscriptionSerializer({"status": "none"}).data

    return SubscriptionSerializer(
        {
            "status": get_subscription_status(subscription=subscription),
            "is_trial": is_trial_subscription(subscription=subscription),
            "plan_name": subscription.plan_name,
            "main_link": subscription.main_url,
            "active_until": subscription.ends_at,
            "remaining_days": subscription.remaining_days,
            "max_devices": subscription.max_devices,
            "countries": subscription.routes.all(),
        }
    ).data


class SubscriptionPlanSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    duration_days = serializers.IntegerField()
    price_rub = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    description = serializers.CharField()


class PurchaseSubscriptionSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=16)


class SubscriptionCheckoutSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    checkout_url = serializers.URLField()
    status = serializers.CharField()
    provider = serializers.CharField()
    payment_method = serializers.CharField()
    plan_code = serializers.CharField()
