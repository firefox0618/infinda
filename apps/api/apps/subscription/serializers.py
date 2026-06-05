from rest_framework import serializers

from .models import Subscription, SubscriptionRoute


class SubscriptionRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionRoute
        fields = ("code", "label", "url")


class SubscriptionSerializer(serializers.Serializer):
    plan_name = serializers.CharField()
    main_link = serializers.URLField()
    active_until = serializers.DateField()
    remaining_days = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    countries = SubscriptionRouteSerializer(many=True)


def serialize_subscription(*, subscription: Subscription) -> dict:
    return SubscriptionSerializer(
        {
            "plan_name": subscription.plan_name,
            "main_link": subscription.main_url,
            "active_until": subscription.ends_at,
            "remaining_days": subscription.remaining_days,
            "max_devices": subscription.max_devices,
            "countries": subscription.routes.all(),
        }
    ).data
