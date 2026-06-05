from django.urls import path

from .views import (
    CurrentSubscriptionView,
    PlategaWebhookView,
    SubscriptionCheckoutView,
    SubscriptionPlansView,
)


urlpatterns = [
    path("", CurrentSubscriptionView.as_view(), name="subscription-current"),
    path("plans/", SubscriptionPlansView.as_view(), name="subscription-plans"),
    path("checkout/", SubscriptionCheckoutView.as_view(), name="subscription-checkout"),
    path(
        "webhooks/platega/<str:secret>/",
        PlategaWebhookView.as_view(),
        name="subscription-platega-webhook",
    ),
]
