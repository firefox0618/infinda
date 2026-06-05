from django.shortcuts import get_object_or_404

from .models import Subscription


def get_user_subscription(*, user):
    return get_object_or_404(
        Subscription.objects.prefetch_related("routes"),
        user=user,
    )
