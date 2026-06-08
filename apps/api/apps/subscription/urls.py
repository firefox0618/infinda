from django.urls import path

from .views import (
    AdminSubscriptionPaymentListView,
    AdminSubscriptionPaymentStatusView,
    CurrentSubscriptionView,
    PlategaWebhookView,
    PublicSubscriptionFeedView,
    PublicSubscriptionSummaryView,
    PublicSubscriptionTouchView,
    SubscriptionCheckoutView,
    SubscriptionPlansView,
)


urlpatterns = [
    path("", CurrentSubscriptionView.as_view(), name="subscription-current"),
    path("admin/payments/", AdminSubscriptionPaymentListView.as_view(), name="subscription-admin-payments"),
    path(
        "admin/payments/<int:payment_id>/status/",
        AdminSubscriptionPaymentStatusView.as_view(),
        name="subscription-admin-payment-status",
    ),
    path("public/<str:token>/feed/", PublicSubscriptionFeedView.as_view(), name="subscription-public-feed"),
    path("public/<str:token>/summary/", PublicSubscriptionSummaryView.as_view(), name="subscription-public-summary"),
    path("public/<str:token>/touch/", PublicSubscriptionTouchView.as_view(), name="subscription-public-touch"),
    path("plans/", SubscriptionPlansView.as_view(), name="subscription-plans"),
    path("checkout/", SubscriptionCheckoutView.as_view(), name="subscription-checkout"),
    path(
        "webhooks/platega/<str:secret>/",
        PlategaWebhookView.as_view(),
        name="subscription-platega-webhook",
    ),
]
