from rest_framework import serializers

from .link_builders import (
    build_public_subscription_client_links,
    build_client_links_for_source_url,
    build_public_subscription_feed_url,
    build_public_subscription_happ_deep_link,
    build_public_subscription_happ_routing_link,
    build_public_subscription_happ_wrapper_url,
    build_public_subscription_install_guides,
)
from .models import Subscription, SubscriptionHistoryEvent, SubscriptionPayment, SubscriptionRoute
from .services import (
    build_subscription_route_access_snapshot,
    get_latest_pending_subscription_payment,
    get_subscription_status,
    is_trial_subscription,
    list_subscription_history,
    list_subscription_payments,
)


class SubscriptionRouteSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    url = serializers.CharField()
    is_provisioned = serializers.BooleanField()
    client_links = serializers.SerializerMethodField()

    def get_client_links(self, obj: dict) -> list[dict[str, str]]:
        return build_client_links_for_source_url(source_url=obj["url"], code_prefix=obj["code"])


class SubscriptionClientLinkSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    kind = serializers.ChoiceField(choices=("happ", "generic", "routing"))
    url = serializers.CharField()


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


class OperatorSubscriptionPaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = SubscriptionPayment
        fields = (
            "id",
            "user_email",
            "plan_code",
            "plan_name",
            "amount_rub",
            "status",
            "provider",
            "payment_method",
            "provider_status",
            "external_payment_id",
            "checkout_url",
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
    feed_link = serializers.URLField()
    happ_link = serializers.URLField()
    happ_deep_link = serializers.CharField()
    happ_routing_link = serializers.CharField()
    client_links = SubscriptionClientLinkSerializer(many=True)
    active_until = serializers.DateField()
    remaining_days = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    uses_provisioned_access = serializers.BooleanField()
    provisioned_route_count = serializers.IntegerField()
    resolved_device_name = serializers.CharField(allow_null=True)
    countries = SubscriptionRouteSerializer(many=True)
    payment_history = SubscriptionPaymentHistorySerializer(many=True)
    subscription_history = SubscriptionHistoryEventSerializer(many=True)
    pending_payment = SubscriptionPaymentHistorySerializer(allow_null=True)


class EmptySubscriptionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("none", "pending_payment"))
    pending_payment = SubscriptionPaymentHistorySerializer(allow_null=True)


def serialize_subscription(
    *,
    subscription: Subscription | None,
    user=None,
    request_ip: str | None = None,
    request_device_key: str | None = None,
) -> dict:
    if subscription is None:
        pending_payment = get_latest_pending_subscription_payment(user=user) if user is not None else None
        return EmptySubscriptionSerializer(
            {
                "status": "pending_payment" if pending_payment is not None else "none",
                "pending_payment": pending_payment,
            }
        ).data

    snapshot = build_subscription_route_access_snapshot(
        subscription=subscription,
        request_ip=request_ip,
        request_device_key=request_device_key,
    )
    return SubscriptionSerializer(
        {
            "status": get_subscription_status(subscription=subscription, user=subscription.user),
            "is_trial": is_trial_subscription(subscription=subscription),
            "plan_name": subscription.plan_name,
            "main_link": subscription.main_url,
            "feed_link": build_public_subscription_feed_url(token=subscription.public_token),
            "happ_link": build_public_subscription_happ_wrapper_url(token=subscription.public_token),
            "happ_deep_link": build_public_subscription_happ_deep_link(token=subscription.public_token),
            "happ_routing_link": build_public_subscription_happ_routing_link(),
            "client_links": build_public_subscription_client_links(token=subscription.public_token),
            "active_until": subscription.ends_at,
            "remaining_days": subscription.remaining_days,
            "max_devices": subscription.max_devices,
            "uses_provisioned_access": snapshot["uses_provisioned_access"],
            "provisioned_route_count": snapshot["provisioned_route_count"],
            "resolved_device_name": (
                snapshot["resolved_device"].resolved_display_name
                if snapshot["resolved_device"] is not None
                else None
            ),
            "countries": snapshot["routes"],
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


class OperatorSubscriptionPaymentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("paid", "canceled", "failed"))


class PublicSubscriptionActionLinkSerializer(serializers.Serializer):
    label = serializers.CharField()
    url = serializers.URLField()


class PublicSubscriptionInstallGuideSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    links = PublicSubscriptionActionLinkSerializer(many=True)


class PublicSubscriptionSummarySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("trial", "active", "expired", "pending_payment"))
    is_trial = serializers.BooleanField()
    plan_name = serializers.CharField()
    main_link = serializers.URLField()
    feed_link = serializers.URLField()
    happ_link = serializers.URLField()
    happ_deep_link = serializers.CharField()
    happ_routing_link = serializers.CharField()
    client_links = SubscriptionClientLinkSerializer(many=True)
    active_until = serializers.DateField()
    remaining_days = serializers.IntegerField()
    max_devices = serializers.IntegerField()
    uses_provisioned_access = serializers.BooleanField()
    provisioned_route_count = serializers.IntegerField()
    resolved_device_name = serializers.CharField(allow_null=True)
    install_guides = PublicSubscriptionInstallGuideSerializer(many=True)
    countries = SubscriptionRouteSerializer(many=True)


class PublicSubscriptionTouchRequestSerializer(serializers.Serializer):
    device_name = serializers.CharField(required=False, allow_blank=True, max_length=120)
    platform = serializers.CharField(required=False, allow_blank=True, max_length=80)
    client = serializers.CharField(required=False, allow_blank=True, max_length=80)
    icon = serializers.ChoiceField(
        required=False,
        choices=("desktop", "mobile", "laptop"),
    )


class PublicSubscriptionTouchDeviceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    platform = serializers.CharField()
    client = serializers.CharField()
    ip = serializers.CharField()


class PublicSubscriptionTouchResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    created = serializers.BooleanField()
    scheduled_operation_count = serializers.IntegerField()
    failed_operation_count = serializers.IntegerField()
    device = PublicSubscriptionTouchDeviceSerializer()


def serialize_public_subscription_summary(
    *,
    subscription: Subscription,
    request_ip: str | None = None,
    request_device_key: str | None = None,
) -> dict:
    snapshot = build_subscription_route_access_snapshot(
        subscription=subscription,
        request_ip=request_ip,
        request_device_key=request_device_key,
    )
    return PublicSubscriptionSummarySerializer(
        {
            "status": get_subscription_status(subscription=subscription, user=subscription.user),
            "is_trial": is_trial_subscription(subscription=subscription),
            "plan_name": subscription.plan_name,
            "main_link": subscription.main_url,
            "feed_link": build_public_subscription_feed_url(token=subscription.public_token),
            "happ_link": build_public_subscription_happ_wrapper_url(token=subscription.public_token),
            "happ_deep_link": build_public_subscription_happ_deep_link(token=subscription.public_token),
            "happ_routing_link": build_public_subscription_happ_routing_link(),
            "client_links": build_public_subscription_client_links(token=subscription.public_token),
            "active_until": subscription.ends_at,
            "remaining_days": subscription.remaining_days,
            "max_devices": subscription.max_devices,
            "uses_provisioned_access": snapshot["uses_provisioned_access"],
            "provisioned_route_count": snapshot["provisioned_route_count"],
            "resolved_device_name": (
                snapshot["resolved_device"].resolved_display_name
                if snapshot["resolved_device"] is not None
                else None
            ),
            "install_guides": build_public_subscription_install_guides(),
            "countries": snapshot["routes"],
        }
    ).data
