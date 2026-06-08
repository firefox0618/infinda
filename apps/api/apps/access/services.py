from apps.devices.models import Device
from apps.provisioning.services import build_user_provisioning_summary
from apps.routing.models import ConnectionRoute
from apps.servers.models import Server
from apps.subscription.services import (
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_EXPIRED,
    SUBSCRIPTION_STATUS_PENDING_PAYMENT,
    SUBSCRIPTION_STATUS_TRIAL,
    get_latest_pending_subscription_payment,
    get_subscription_status,
    get_user_subscription,
)


ACCESS_STATUS_ACTIVE = "active"
ACCESS_STATUS_EXPIRED = "expired"
ACCESS_STATUS_PENDING_PAYMENT = "pending_payment"
ACCESS_STATUS_DEVICE_LIMIT_EXCEEDED = "device_limit_exceeded"
ACCESS_STATUS_RESTRICTED = "restricted"
ACCESS_STATUS_SERVER_UNAVAILABLE = "server_unavailable"


def list_subscription_connection_routes(*, subscription):
    return (
        subscription.routes.select_related("connection_route__location", "connection_route__server")
        .filter(connection_route__isnull=False)
        .order_by("position", "id")
    )


def build_user_access_state(*, user) -> dict:
    subscription = get_user_subscription(user=user)
    pending_payment = get_latest_pending_subscription_payment(user=user)
    subscription_status = (
        get_subscription_status(subscription=subscription, user=user)
        if subscription is not None or pending_payment is not None
        else "none"
    )

    active_device_count = Device.objects.filter(user=user, revoked_at__isnull=True).count()
    allowed_device_count = subscription.max_devices if subscription is not None else 0
    provisioning_summary = build_user_provisioning_summary(user=user)

    if pending_payment is not None and subscription is None:
        return {
            "status": ACCESS_STATUS_PENDING_PAYMENT,
            "reason": "pending_payment_without_subscription",
            "subscription_status": SUBSCRIPTION_STATUS_PENDING_PAYMENT,
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": [],
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    if subscription is None:
        return {
            "status": ACCESS_STATUS_RESTRICTED,
            "reason": "no_subscription",
            "subscription_status": "none",
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": [],
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    if subscription_status == SUBSCRIPTION_STATUS_EXPIRED:
        return {
            "status": ACCESS_STATUS_EXPIRED,
            "reason": "subscription_expired",
            "subscription_status": subscription_status,
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": [],
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    if subscription_status == SUBSCRIPTION_STATUS_PENDING_PAYMENT:
        return {
            "status": ACCESS_STATUS_PENDING_PAYMENT,
            "reason": "subscription_payment_pending",
            "subscription_status": subscription_status,
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": [],
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    if active_device_count > allowed_device_count:
        return {
            "status": ACCESS_STATUS_DEVICE_LIMIT_EXCEEDED,
            "reason": "device_limit_exceeded",
            "subscription_status": subscription_status,
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": [],
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    assigned_routes = list_subscription_connection_routes(subscription=subscription)
    if not assigned_routes.exists():
        return {
            "status": ACCESS_STATUS_RESTRICTED,
            "reason": "no_routes_assigned",
            "subscription_status": subscription_status,
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": [],
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    available_routes = assigned_routes.filter(
        connection_route__is_active=True,
        connection_route__location__is_active=True,
        connection_route__server__status__in=(
            Server.Status.ACTIVE,
            Server.Status.DEGRADED,
        ),
    )
    unavailable_route_codes = [
        route.code for route in assigned_routes.exclude(id__in=available_routes.values("id"))
    ]

    if not available_routes.exists():
        return {
            "status": ACCESS_STATUS_SERVER_UNAVAILABLE,
            "reason": "all_servers_unavailable",
            "subscription_status": subscription_status,
            "active_device_count": active_device_count,
            "allowed_device_count": allowed_device_count,
            "available_route_count": 0,
            "unavailable_route_codes": unavailable_route_codes,
            "provisioning_issue_count": provisioning_summary["failed_operation_count"],
            "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
            "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
            "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
            "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
            "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
        }

    return {
        "status": ACCESS_STATUS_ACTIVE,
        "reason": (
            "trial_active" if subscription_status == SUBSCRIPTION_STATUS_TRIAL else "subscription_active"
        ),
        "subscription_status": subscription_status,
        "active_device_count": active_device_count,
        "allowed_device_count": allowed_device_count,
        "available_route_count": available_routes.count(),
        "unavailable_route_codes": unavailable_route_codes,
        "provisioning_issue_count": provisioning_summary["failed_operation_count"],
        "last_provisioning_error_codes": provisioning_summary["last_error_codes"],
        "active_provisioned_binding_count": provisioning_summary["active_binding_count"],
        "error_provisioned_binding_count": provisioning_summary["error_binding_count"],
        "unhealthy_provisioning_server_count": provisioning_summary["unhealthy_server_count"],
        "degraded_provisioning_server_count": provisioning_summary["degraded_server_count"],
    }
