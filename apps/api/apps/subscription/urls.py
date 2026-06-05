from django.urls import path

from .views import (
    CurrentSubscriptionView,
    PlategaWebhookView,
    PurchaseSubscriptionView,
    SubscriptionCheckoutView,
    SubscriptionPlansView,
)


urlpatterns = [
    path("", CurrentSubscriptionView.as_view(), name="subscription-current"),
    path("plans/", SubscriptionPlansView.as_view(), name="subscription-plans"),
    path("checkout/", SubscriptionCheckoutView.as_view(), name="subscription-checkout"),
    path("purchase/", PurchaseSubscriptionView.as_view(), name="subscription-purchase"),
    path(
        "webhooks/platega/<str:secret>/",
        PlategaWebhookView.as_view(),
        name="subscription-platega-webhook",
    ),
]
